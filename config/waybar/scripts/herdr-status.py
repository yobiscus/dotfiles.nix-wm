#!/usr/bin/env python3
"""Stream Waybar JSON from local hc facts. Use --once for a single snapshot.

Counts include workers. Completed turns already marked herdr.seen are idle;
unseen completed turns are done. Machine exclusions affect the display only.
Keep the old state filename so existing local exclusions survive the upgrade.
"""

import fcntl
import html
import json
import os
import selectors
import shutil
import signal
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HC = shutil.which("hc") or str(Path.home() / ".local/bin/hc")
STATE_PATH = (
    Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    / "waybar/herdr-status-polling.json"
)
STATUSES = ("working", "done", "idle", "blocked", "error", "unknown")
STATUS_ICONS = {
    "working": "\uf110",
    "done": "\uf0f3",
    "blocked": "\uf071",
    "error": "\uf06a",
    "unknown": "\uf059",
}
ROBOT_ICON = "\uf544"
REFRESH_EVENTS = {
    "created", "restarted", "finished", "lost", "removed", "status", "labels", "turn"
}
DEBOUNCE = 0.2
RETRY_DELAY = 2
STATE_INTERVAL = 1
HEALTH_INTERVAL = 15
EVENT_TIMEOUT = 45


def core_snapshot():
    # hc ls summarizes reports but omits labels; terminal.list includes seen turns.
    request = {"jsonrpc": "2.0", "id": 1, "method": "terminal.list", "params": {}}
    result = subprocess.run(
        (HC, "connect"), input=json.dumps(request) + "\n",
        capture_output=True, check=True, text=True, timeout=5,
    )
    reply = json.loads(result.stdout)
    if "error" in reply:
        raise ValueError("hc terminal.list failed")
    return reply["result"]


def agent_status(terminal):
    report = terminal.get("status")
    status = report.get("state") if isinstance(report, dict) else report
    if status not in {"idle", "done"}:
        return status
    try:
        seen = int(terminal.get("labels", {}).get("herdr.seen"))
    except (TypeError, ValueError):
        return status
    if seen < 0:
        return status
    return "done" if terminal.get("turn", 0) > seen else "idle"


def read_disabled(path=STATE_PATH):
    try:
        disabled = json.loads(path.read_text()).get("disabled", [])
        if not isinstance(disabled, list):
            return set()
        return {key for key in disabled if isinstance(key, str)}
    except (OSError, ValueError, AttributeError):
        return set()


def machine_key(name):
    return "local" if name is None else f"machine:{name}"


def count_text(counts):
    parts = [f"{counts[state]} {state}" for state in STATUSES if counts[state]]
    return ", ".join(parts) or "no agents"


def render(snapshot, disabled):
    machines = {None: "connected"}
    machines.update((m["name"], m["state"]) for m in snapshot.get("machines", []))
    per_machine = {name: Counter() for name in machines}
    for terminal in snapshot["terminals"]:
        status = agent_status(terminal)
        if terminal["state"] != "live" or status is None:
            continue
        address = terminal["address"]
        name = address.split("/", 1)[0] if "/" in address else None
        if name in per_machine:
            per_machine[name][status if status in STATUSES else "unknown"] += 1

    counts = Counter()
    details = []
    partial = False
    for name, state in machines.items():
        if machine_key(name) in disabled:
            detail = "excluded"
        elif state != "connected":
            detail = state
            partial = True
        else:
            counts.update(per_machine[name])
            detail = count_text(per_machine[name])
        details.append(f"  {html.escape(name or 'local')}: {html.escape(detail)}")

    statuses = "  ".join(
        f"{icon}\u2009{counts[state]}" for state, icon in STATUS_ICONS.items() if counts[state]
    )
    text = f"{ROBOT_ICON}\u2009{sum(counts.values())}"
    if statuses:
        text += f"<span size='small' weight='normal'>\u2009\u2009{statuses}</span>"
    if partial:
        text += f"  {STATUS_ICONS['blocked']}"
    priority = ("blocked", "error", "done", "working", "unknown", "idle")
    css_class = next((state for state in priority if counts[state]), "idle")
    return {
        "text": text,
        "tooltip": "\n".join([f"Herdr: {count_text(counts)}", *details]),
        "class": [css_class, "partial"] if partial else css_class,
    }


def unavailable():
    return {
        "text": f"{ROBOT_ICON}\u2009!",
        "tooltip": "Herdr: local core unavailable; reconnecting",
        "class": "unavailable",
    }


def needs_refresh(message):
    return (
        "terminals" in message
        or message.get("method") in {"missed", "heartbeat"}
        or (
            message.get("method") == "event"
            and message["params"].get("type") in REFRESH_EVENTS
        )
    )


def follow(stream, emit, state_path=STATE_PATH, fetch=core_snapshot):
    os.set_blocking(stream.fileno(), False)
    buffer = b""
    last_message = next_state_check = time.monotonic()
    last_refresh = None
    pending = None
    disabled = read_disabled(state_path)
    with selectors.DefaultSelector() as selector:
        selector.register(stream, selectors.EVENT_READ)
        while True:
            now = time.monotonic()
            if now - last_message >= EVENT_TIMEOUT:
                raise TimeoutError("hc event stream stopped responding")
            if now >= next_state_check:
                current = read_disabled(state_path)
                if current != disabled:
                    disabled, pending = current, now
                next_state_check = now + STATE_INTERVAL
            # ponytail: poll connection states after 15s without a snapshot;
            # replace this fallback if core adds machine connection events.
            if pending is None and last_refresh is not None and now - last_refresh >= HEALTH_INTERVAL:
                pending = now
            if pending is not None and now >= pending:
                emit(render(fetch(), disabled))
                last_refresh = time.monotonic()
                pending = None
            deadline = min(next_state_check, pending) if pending is not None else next_state_check
            timeout = max(0, deadline - time.monotonic())
            if not selector.select(timeout):
                continue
            chunk = os.read(stream.fileno(), 65536)
            if not chunk:
                raise EOFError("hc event stream closed")
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("expected an hc JSON object")
                last_message = time.monotonic()
                if needs_refresh(message) and pending is None:
                    pending = last_message
                    if "terminals" not in message:
                        pending += DEBOUNCE


def watch(state_path=STATE_PATH):
    previous = None

    def emit(value):
        nonlocal previous
        if value != previous:
            print(json.dumps(value, separators=(",", ":")), flush=True)
            previous = value

    while True:
        client = None
        try:
            client = subprocess.Popen(
                (HC, "events", "--json"), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, bufsize=0,
            )
            follow(client.stdout, emit, state_path)
        except (OSError, ValueError, KeyError, TypeError, EOFError, subprocess.SubprocessError):
            emit(unavailable())
        finally:
            if client is not None:
                if client.poll() is None:
                    client.terminate()
                    try:
                        client.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        client.kill()
                        client.wait()
                client.stdout.close()
        time.sleep(RETRY_DELAY)


def choose_machine(entries):
    result = subprocess.run(
        ("wofi", "--dmenu", "--prompt", "Herdr machines"),
        input="\n".join(entries), capture_output=True, text=True,
    )
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def machine_menu(state_path=STATE_PATH, fetch=core_snapshot, choose=choose_machine):
    snapshot = fetch()
    disabled = read_disabled(state_path)
    machines = [(None, "connected")]
    machines.extend((m["name"], m["state"]) for m in snapshot.get("machines", []))
    selections = {}
    for name, state in machines:
        key = machine_key(name)
        marker = "○" if key in disabled else "●"
        label = "local [this machine]" if name is None else name
        selections[f"{marker} {label} ({state})"] = key
    selected = choose(list(selections))
    if selected not in selections:
        return False
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        disabled = read_disabled(state_path)
        key = selections[selected]
        disabled.symmetric_difference_update({key})
        temporary = state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"disabled": sorted(disabled)}))
        temporary.replace(state_path)
    return True


def main():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        if sys.argv[1:] == ["menu"]:
            machine_menu()
        elif sys.argv[1:] == ["--once"]:
            result = render(core_snapshot(), read_disabled())
            print(json.dumps(result, separators=(",", ":")))
        elif not sys.argv[1:]:
            watch()
        else:
            raise SystemExit(f"usage: {Path(sys.argv[0]).name} [menu | --once]")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps(unavailable()), flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass

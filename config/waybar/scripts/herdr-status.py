#!/usr/bin/env python3

import fcntl
import json
import os
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

STATUSES = ("working", "done", "idle", "blocked", "unknown")
ROBOT_ICON = "\uf544"
STATUS_ICONS = {
    "working": "\uf110",
    "done": "\uf0f3",
    "blocked": "\uf071",
    "unknown": "\uf059",
}
SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=2",
    "-o",
    "ControlMaster=auto",
    "-o",
    "ControlPersist=60",
    "-o",
    "ControlPath=~/.ssh/herdr-%C",
)
HERDR = 'PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:$PATH" herdr'
CACHE_PATH = Path.home() / ".cache/waybar/herdr-status.json"
STATE_PATH = (
    Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    / "waybar/herdr-status-polling.json"
)
LOCAL_MACHINE = {
    "id": "local",
    "label": "local",
    "target": None,
    "session": "default",
    "enabled": True,
}


def command_json(target, command):
    if target is None:
        args = ("herdr", *shlex.split(command))
    else:
        args = ("ssh", *SSH_OPTIONS, "--", target, f"{HERDR} {command}")
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return json.loads(result.stdout)
    except (OSError, UnicodeError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def machine_catalog(fetch=command_json):
    response = fetch(None, "machine list --json")
    if not isinstance(response, list):
        return None

    machines = []
    for machine in response:
        if not isinstance(machine, dict):
            continue
        machine_id = machine.get("id")
        target = machine.get("target")
        session = machine.get("session", "default")
        label = machine.get("label", target)
        enabled = machine.get("enabled")
        fields = (machine_id, label, target, session)
        if not all(isinstance(value, str) and value for value in fields) or not isinstance(
            enabled, bool
        ):
            continue
        machines.append(
            {
                "id": machine_id,
                "label": label,
                "target": target,
                "session": session,
                "enabled": enabled,
            }
        )
    return machines


def collect(remotes, disabled, fetch=command_json):
    counts = Counter()
    machines = []
    reachable = 0

    for machine in [LOCAL_MACHINE, *remotes]:
        machine_id = machine["id"]
        label = machine["label"]
        target = machine["target"]
        session = machine["session"]
        if machine_id in disabled:
            machines.append((label, "polling disabled"))
            continue
        if not machine["enabled"]:
            machines.append((label, "disabled in Herdr"))
            continue

        response = fetch(target, f"--session {shlex.quote(session)} agent list")
        try:
            agents = response["result"]["agents"]
            if not isinstance(agents, list):
                raise TypeError
        except (KeyError, TypeError):
            machines.append((label, None))
            continue

        reachable += 1
        session_counts = Counter(
            agent.get("agent_status", "unknown")
            if isinstance(agent, dict) and agent.get("agent_status") in STATUSES
            else "unknown"
            for agent in agents
        )
        counts.update(session_counts)
        machines.append((label, [(session, session_counts)]))

    return counts, machines, reachable


def count_text(counts):
    parts = [f"{counts[status]} {status}" for status in STATUSES if counts[status]]
    return ", ".join(parts) or "no agents"


def bar_text(counts):
    statuses = "  ".join(
        f"{icon}\u2009{counts[status]}"
        for status, icon in STATUS_ICONS.items()
        if counts[status]
    )
    detail = f"<span size='small' weight='normal'>\u2009\u2009{statuses}</span>" if statuses else ""
    return f"{ROBOT_ICON}\u2009{sum(counts.values())}{detail}"


def render(counts, machines, reachable):
    priority = ("blocked", "done", "working", "unknown", "idle")
    if not reachable and any(not isinstance(state, str) for _, state in machines):
        css_class = "unavailable"
    else:
        css_class = next((status for status in priority if counts[status]), "idle")
    lines = [f"Herdr: {count_text(counts)}"]
    for label, sessions in machines:
        if isinstance(sessions, str):
            lines.append(f"  {label}: {sessions}")
            continue
        if sessions is None:
            lines.append(f"  {label}: unavailable")
            continue
        lines.append(f"  {label}")
        for name, session_counts in sessions:
            detail = "unavailable" if session_counts is None else count_text(session_counts)
            lines.append(f"    {name}: {detail}")

    return {
        "text": bar_text(counts),
        "tooltip": "\n".join(lines),
        "class": css_class,
    }


def read_cache(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def read_disabled(path=STATE_PATH):
    try:
        value = json.loads(path.read_text())
        disabled = value.get("disabled", [])
        if not isinstance(disabled, list):
            return set()
        return {machine_id for machine_id in disabled if isinstance(machine_id, str)}
    except (AttributeError, OSError, UnicodeError, json.JSONDecodeError):
        return set()


def write_disabled(path, disabled):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"disabled": sorted(disabled)}, separators=(",", ":")))
    temporary.replace(path)


def reconcile_disabled(remotes, state_path=STATE_PATH):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        disabled = read_disabled(state_path)
        known = {LOCAL_MACHINE["id"], *(machine["id"] for machine in remotes)}
        reconciled = disabled & known
        if reconciled != disabled:
            write_disabled(state_path, reconciled)
        return reconciled


def choose_machine(entries):
    try:
        result = subprocess.run(
            ("wofi", "--dmenu", "--prompt", "Herdr polling"),
            input="\n".join(entries),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def polling_menu(state_path=STATE_PATH, fetch=command_json, choose=choose_machine):
    remotes = machine_catalog(fetch)
    if remotes is None:
        return False

    disabled = reconcile_disabled(remotes, state_path)
    machines = [LOCAL_MACHINE, *(machine for machine in remotes if machine["enabled"])]
    selections = {}
    for machine in machines:
        marker = "○" if machine["id"] in disabled else "●"
        if machine["target"] is None:
            detail = "local"
        else:
            detail = f"{machine['target']}/{machine['session']}"
        entry = f"{marker} {machine['label']} — {detail} [{machine['id'][:8]}]"
        selections[entry] = machine["id"]

    selected = choose(list(selections))
    if selected not in selections:
        return False

    machine_id = selections[selected]
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        disabled = read_disabled(state_path)
        if machine_id in disabled:
            disabled.remove(machine_id)
        else:
            disabled.add(machine_id)
        write_disabled(state_path, disabled)
    return True


def refresh(cache_path=CACHE_PATH, state_path=STATE_PATH, fetch=command_json):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.with_suffix(".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return read_cache(cache_path) or render(Counter(), [], 0)

        remotes = machine_catalog(fetch)
        if remotes is None:
            return read_cache(cache_path) or render(Counter(), [], 0)

        disabled = reconcile_disabled(remotes, state_path)
        collected = collect(remotes, disabled, fetch)
        result = render(*collected)
        temporary = cache_path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(result, separators=(",", ":")))
            temporary.replace(cache_path)
        except OSError:
            pass
        return result


def main():
    if sys.argv[1:] == ["menu"]:
        polling_menu()
    elif sys.argv[1:]:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} [menu]")
    else:
        print(json.dumps(refresh(), separators=(",", ":")))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import fcntl
import json
import shlex
import subprocess
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
        if not isinstance(machine, dict) or not machine.get("enabled"):
            continue
        machine_id = machine.get("id")
        target = machine.get("target")
        session = machine.get("session", "default")
        label = machine.get("label", target)
        fields = (machine_id, label, target, session)
        if not all(isinstance(value, str) and value for value in fields):
            continue
        machines.append((machine_id, label, target, session))
    return machines


def collect(fetch=command_json):
    remotes = machine_catalog(fetch)
    if remotes is None:
        return None

    counts = Counter()
    machines = []
    reachable = 0

    targets = [("local", "local", None, "default"), *remotes]
    for _machine_id, label, target, session in targets:
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
    if not reachable:
        return {"text": "", "tooltip": "Herdr: no reachable machines", "class": "unavailable"}

    priority = ("blocked", "done", "working", "unknown", "idle")
    css_class = next((status for status in priority if counts[status]), "idle")
    lines = [f"Herdr: {count_text(counts)}"]
    for label, sessions in machines:
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


def refresh(cache_path=CACHE_PATH, fetch=command_json):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.with_suffix(".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return read_cache(cache_path) or render(Counter(), [], 0)

        collected = collect(fetch)
        if collected is None:
            return read_cache(cache_path) or render(Counter(), [], 0)

        result = render(*collected)
        temporary = cache_path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(result, separators=(",", ":")))
            temporary.replace(cache_path)
        except OSError:
            pass
        return result


def main():
    print(json.dumps(refresh(), separators=(",", ":")))


if __name__ == "__main__":
    main()

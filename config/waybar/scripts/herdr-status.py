#!/usr/bin/env python3

import fcntl
import json
import shlex
import subprocess
import tomllib
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

# Only the default session is considered. If more sessions are needed, use a
# static list or a cached discovery list that updates much less frequently.
SESSION = "default"


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


def inventories(path):
    for inventory in sorted(path.glob("*.toml")):
        try:
            data = tomllib.loads(inventory.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            continue
        machines = data.get("machine", [])
        if not isinstance(machines, list):
            continue
        for machine in machines:
            if not isinstance(machine, dict):
                continue
            target = machine.get("ssh_target")
            if not isinstance(target, str):
                continue
            if isinstance(machine.get("label", target), str):
                yield machine.get("label", target), target


def collect(path, fetch=command_json):
    counts = Counter()
    machines = []
    reachable = 0

    for label, target in [("local", None), *inventories(path)]:
        response = fetch(target, f"--session {SESSION} agent list")
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
        machines.append((label, [(SESSION, session_counts)]))

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


def refresh(inventory_dir, cache_path=CACHE_PATH, fetch=command_json):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.with_suffix(".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return read_cache(cache_path) or render(Counter(), [], 0)

        result = render(*collect(inventory_dir, fetch))
        temporary = cache_path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(result, separators=(",", ":")))
            temporary.replace(cache_path)
        except OSError:
            pass
        return result


def main():
    inventory_dir = Path.home() / ".config/herdr/waybar"
    print(json.dumps(refresh(inventory_dir), separators=(",", ":")))


if __name__ == "__main__":
    main()

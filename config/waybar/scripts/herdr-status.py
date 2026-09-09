#!/usr/bin/env python3

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
    "idle": "\uf111",
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
        listing = fetch(target, "session list --json")
        if not isinstance(listing, dict) or not isinstance(listing.get("sessions"), list):
            machines.append((label, None))
            continue

        reachable += 1
        sessions = []
        for session in listing["sessions"]:
            if (
                not isinstance(session, dict)
                or not session.get("running")
                or not isinstance(session.get("name"), str)
            ):
                continue
            name = session["name"]
            response = fetch(target, f"--session {shlex.quote(name)} api snapshot")
            try:
                agents = response["result"]["snapshot"]["agents"]
                if not isinstance(agents, list):
                    raise TypeError
            except (KeyError, TypeError):
                sessions.append((name, None))
                continue

            session_counts = Counter(
                agent.get("agent_status", "unknown")
                if isinstance(agent, dict) and agent.get("agent_status") in STATUSES
                else "unknown"
                for agent in agents
            )
            counts.update(session_counts)
            sessions.append((name, session_counts))
        machines.append((label, sessions))

    return counts, machines, reachable


def count_text(counts):
    parts = [f"{counts[status]} {status}" for status in STATUSES if counts[status]]
    return ", ".join(parts) or "no agents"


def bar_text(counts):
    statuses = "  ".join(
        f"{STATUS_ICONS[status]} {counts[status]}"
        for status in STATUSES
        if counts[status]
    )
    return f"{ROBOT_ICON} {statuses}".rstrip()


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


def main():
    inventory_dir = Path.home() / ".config/herdr/waybar"
    print(json.dumps(render(*collect(inventory_dir)), separators=(",", ":")))


if __name__ == "__main__":
    main()

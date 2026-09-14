#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ASSET_DIR = Path.home() / ".config/waybar/assets"
CISCO_SSIDS = {"blizzard", "blizzard@home"}


def run(*command: str) -> str:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def tailscale_status() -> dict:
    try:
        return json.loads(run("tailscale", "status", "--json"))
    except (json.JSONDecodeError, TypeError):
        return {}


def active_connections() -> list[str]:
    return run("nmcli", "-g", "NAME", "connection", "show", "--active").splitlines()


def active_ssid() -> str:
    output = run(
        "nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi", "list", "--rescan", "no"
    )
    for line in output.splitlines():
        if line.startswith("yes:"):
            return line.removeprefix("yes:")
    return ""


def show(name: str, tooltip: str) -> None:
    print(ASSET_DIR / f"{name}.svg")
    print(tooltip)


def hide() -> None:
    # Waybar 0.15 retains the previous path when a script prints nothing.
    print("/nonexistent/waybar-vpn-status")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"tailscale", "cisco", "pia"}:
        raise SystemExit("usage: vpn-status.py {tailscale|cisco|pia}")

    provider = sys.argv[1]

    if provider == "tailscale":
        if tailscale_status().get("BackendState") == "Running":
            show("tailscale", "Tailnet connected")
        else:
            hide()
        return

    connections = active_connections()

    if provider == "cisco":
        ssid = active_ssid()
        cisco_vpn = any(
            re.search(r"cisco|anyconnect", name, re.IGNORECASE) for name in connections
        )
        cisco_wifi = ssid.casefold() in CISCO_SSIDS
        if not (cisco_vpn or cisco_wifi):
            hide()
            return

        details = []
        if cisco_vpn:
            details.append("Cisco VPN connected")
        if cisco_wifi:
            details.append(f"Cisco network: {ssid}")
        show("cisco", " — ".join(details))
        return

    pia_state = run("piactl", "get", "connectionstate").casefold()
    pia_connection = any(
        re.search(r"(^|[^a-z])pia([^a-z]|$)|private internet access", name, re.IGNORECASE)
        for name in connections
    )
    if pia_state == "connected" or pia_connection:
        show("pia", "PIA connected")
    else:
        hide()


if __name__ == "__main__":
    main()

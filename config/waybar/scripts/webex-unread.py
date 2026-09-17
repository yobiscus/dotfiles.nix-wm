#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

PROCESS_NAME = "CiscoCollabHost"
LOG_PATH = Path.home() / ".local/share/Webex/current_log.txt"
ICON_PATH = Path.home() / ".local/share/WebexLauncher/sparklogosmall.png"
COUNT_PATTERN = re.compile(rb"all unread messages count in filter is (\d+)")


def webex_running(proc_root=Path("/proc")):
    for process in proc_root.glob("[0-9]*"):
        try:
            owned = process.stat().st_uid == os.getuid()
            named = (process / "comm").read_text().strip() == PROCESS_NAME
            if owned and named:
                return True
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return False


def unread_count(path=LOG_PATH):
    overlap = 128
    with path.open("rb") as log:
        log.seek(0, os.SEEK_END)
        position = log.tell()
        suffix = b""
        while position:
            size = min(64 * 1024, position)
            position -= size
            log.seek(position)
            block = log.read(size) + suffix
            matches = list(COUNT_PATTERN.finditer(block))
            if matches:
                return int(matches[-1].group(1))
            suffix = block[:overlap]
    raise ValueError("no unread count found in Webex log")


def error_message(error):
    if isinstance(error, FileNotFoundError):
        detail = "Webex log not found"
    elif isinstance(error, PermissionError):
        detail = "Webex log is not readable"
    else:
        detail = str(error)
    return f"Webex unread count unavailable: {detail}"


def status(running=webex_running, read_count=unread_count):
    if not running():
        return {"text": "", "tooltip": "", "class": "hidden"}
    try:
        count = read_count()
    except (OSError, ValueError) as error:
        message = error_message(error)
        return {"text": "!", "tooltip": message, "class": "error"}

    noun = "space" if count == 1 else "spaces"
    return {
        "text": str(count) if count else "",
        "tooltip": f"Webex: {count} unread {noun}",
        "class": "unread" if count else "read",
    }


def icon(running=webex_running, read_count=unread_count):
    if not running():
        return ""
    try:
        count = read_count()
        noun = "space" if count == 1 else "spaces"
        tooltip = f"Webex: {count} unread {noun}"
    except (OSError, ValueError) as error:
        tooltip = error_message(error)
    return f"{ICON_PATH}\n{tooltip}"


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "icon":
        print(icon())
    else:
        print(json.dumps(status(), separators=(",", ":")))

#!/bin/bash

set -euo pipefail

loginctl lock-session >/dev/null 2>&1 || true

if ! pgrep -x hyprlock >/dev/null; then
    hyprlock --no-fade-in >/dev/null 2>&1 &
fi

for ((i=0; i<20; i++)); do
    if pgrep -x hyprlock >/dev/null; then
        sleep 0.2
        break
    fi
    sleep 0.1
done

systemctl suspend

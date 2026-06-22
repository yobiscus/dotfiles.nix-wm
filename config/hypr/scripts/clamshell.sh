#!/bin/bash
if [ "$1" = "close" ]; then
    hyprctl keyword monitor "eDP-1, disable"
elif [ "$1" = "open" ]; then
    # Loop until the kernel detects that the eDP panel is physically connected
    timeout=5
    while [ $timeout -gt 0 ]; do
        if grep -q "connected" /sys/class/drm/card*-eDP-1/status 2>/dev/null; then
            break
        fi
        sleep 0.1
        timeout=$((timeout-1))
    fi

    # Safely re-enable your configuration now that the hardware is ready
    hyprctl keyword monitor "$2"
    hyprctl reload
fi

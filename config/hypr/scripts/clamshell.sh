#!/bin/bash
if [ "$1" = "close" ]; then
    hyprctl eval 'hl.monitor({ output = "eDP-1", disabled = true })'
elif [ "$1" = "open" ]; then
    # Loop until the kernel detects that the eDP panel is physically connected
    timeout=5
    while [ $timeout -gt 0 ]; do
        if grep -qx "connected" /sys/class/drm/card*-eDP-1/status 2>/dev/null; then
            break
        fi
        sleep 0.1
        timeout=$((timeout-1))
    done

    # Reload monitor.lua to restore the configured mode, position and scale.
    hyprctl reload
fi

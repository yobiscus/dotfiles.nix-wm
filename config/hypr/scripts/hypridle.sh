#!/bin/bash
#    __ __              _    ____   
#   / // /_ _____  ____(_)__/ / /__ 
#  / _  / // / _ \/ __/ / _  / / -_)
# /_//_/\_, / .__/_/ /_/\_,_/_/\__/ 
#      /___/_/                      
# 

SERVICE="hypridle"

print_status() {
    if pgrep -x "$SERVICE" >/dev/null ; then
        echo '{"text": "RUNNING", "class": "active", "tooltip": "Screen locking active"}'
    else
        echo '{"text": "NOT RUNNING", "class": "notactive", "tooltip": "Screen locking deactivated"}'
    fi
}

case "$1" in
    status)
        print_status
        ;;
    toggle)
        if pgrep -x "$SERVICE" >/dev/null ; then
            killall "$SERVICE"
            # wait for service to die
            for ((i=0; i<20; i++)); do
                if ! pkill -0 -x "$SERVICE"; then
                    break
                fi
                sleep 0.1
            done
        else
            "$SERVICE" >/dev/null &
            # wait for service to spawn
            for ((i=0; i<20; i++)); do
                if pkill -0 -x "$SERVICE"; then
                    break
                fi
                sleep 0.1
            done
        fi
        pkill -SIGRTMIN+10 -xf waybar;
        ;;
    *)
        echo "Usage: $0 {status|toggle}"
        exit 1
        ;;
esac

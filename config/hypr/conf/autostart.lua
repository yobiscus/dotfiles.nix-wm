-- Run once at session startup, never on config reload.
hl.on("hyprland.start", function()
    hl.exec_cmd("waybar")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("obsidian")
    hl.exec_cmd("/opt/Webex/bin/CiscoCollabHost")
    hl.exec_cmd("spotify")
end)

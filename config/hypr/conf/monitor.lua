-- Monitor positions account for scale.
hl.monitor({ output = "eDP-1", mode = "1920x1200", position = "0x0", scale = 1 })
hl.monitor({
    output = "desc:Samsung Electric Company Odyssey G8 HCNWA02383",
    mode = "3840x2160", position = "1920x-1200", scale = 1.25,
})
hl.monitor({
    output = "desc:ViewSonic Corporation VX2778 Series ULY190760145",
    mode = "2560x1440", position = "1920x-1200", scale = 1,
})

-- Laptop lid switches stay active while locked.
hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd("~/.config/hypr/scripts/clamshell.sh close"), { locked = true })
hl.bind("switch:off:Lid Switch", hl.dsp.exec_cmd("~/.config/hypr/scripts/clamshell.sh open"), { locked = true })

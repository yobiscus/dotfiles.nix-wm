local programs = require("conf.variables")
local mainMod = "SUPER"

-- Apps.
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(programs.terminal))
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(programs.menu))
hl.bind(mainMod .. " + F", hl.dsp.exec_cmd(programs.fileManager))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(programs.browser))
hl.bind(mainMod .. " + G", hl.dsp.exec_cmd("gome open"))

-- Screenshots. SHIFT captures an output; CTRL saves to a file.
hl.bind(mainMod .. " + S", hl.dsp.exec_cmd("hyprshot -m region -m active --clipboard-only"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("hyprshot -m output -m active --clipboard-only"))
hl.bind(mainMod .. " + CTRL + S", hl.dsp.exec_cmd("hyprshot -m region -m active -o ~/Pictures/Screenshots"))
hl.bind(mainMod .. " + CTRL + SHIFT + S", hl.dsp.exec_cmd("hyprshot -m output -m active -o ~/Pictures/Screenshots"))

hl.bind(mainMod .. " + C", hl.dsp.window.close())
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo()) -- dwindle
hl.bind(mainMod .. " + O", hl.dsp.layout("togglesplit")) -- dwindle
hl.bind(mainMod .. " + M", function() hl.config({ general = { layout = "monocle" } }) end)
hl.bind(mainMod .. " + SHIFT + M", function() hl.config({ general = { layout = "dwindle" } }) end)
hl.bind(mainMod .. " + Tab", hl.dsp.layout("cyclenext"))
hl.bind(mainMod .. " + SHIFT + Tab", hl.dsp.layout("cycleprev"))
hl.bind("CTRL + ALT + Q", hl.dsp.exec_cmd("hyprlock"))

-- Focus with hjkl; swap windows with SHIFT + hjkl.
for key, direction in pairs({ H = "left", J = "down", K = "up", L = "right" }) do
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ direction = direction }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.swap({ direction = direction }))
end

-- Hide special workspaces when changing workspace, replacing the __TEMP toggles.
hl.config({ binds = { hide_special_on_workspace_change = true } })
for workspace = 1, 10 do
    local key = workspace % 10
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = workspace }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace }))
end

-- Move the current workspace to the adjacent monitor.
hl.bind(mainMod .. " + CTRL + left", hl.dsp.workspace.move({ monitor = "l" }))
hl.bind(mainMod .. " + CTRL + right", hl.dsp.workspace.move({ monitor = "r" }))

-- IM, mail and terminal overlays.
hl.bind(mainMod .. " + W", hl.dsp.workspace.toggle_special("im"))
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.window.move({ workspace = "special:im" }))
hl.bind(mainMod .. " + E", hl.dsp.workspace.toggle_special("mail"))
hl.bind(mainMod .. " + SHIFT + E", hl.dsp.window.move({ workspace = "special:mail" }))
hl.bind(mainMod .. " + Q", hl.dsp.workspace.toggle_special("term"))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.window.move({ workspace = "special:term" }))

hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Volume and brightness keys repeat and work while locked.
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { locked = true, repeating = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })

hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- Alternatives when hardware keys are unavailable.
hl.bind(mainMod .. " + ALT + space", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind(mainMod .. " + ALT + right", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind(mainMod .. " + ALT + left", hl.dsp.exec_cmd("playerctl previous"), { locked = true })
hl.bind(mainMod .. " + ALT + up", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind(mainMod .. " + ALT + down", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })

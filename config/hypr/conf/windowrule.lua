hl.window_rule({
    name = "pavucontrol",
    match = { class = ".*org.pulseaudio.pavucontrol.*" },
    float = true, size = { 700, 600 }, center = true, pin = true,
})
hl.window_rule({
    name = "waypaper",
    match = { class = ".*waypaper.*" },
    float = true, size = { 900, 700 }, center = true, pin = true,
})
hl.window_rule({
    name = "blueman-manager",
    match = { class = ".*blueman-manager.*" },
    float = true, size = { 800, 600 }, center = true,
})
hl.window_rule({
    name = "gome",
    match = { class = [[^(ca\.jogravel\.Gome)$]] },
    float = true,
})
hl.window_rule({
    name = "dotfiles-floating",
    match = { class = "dotfiles-floating" },
    float = true, size = { 1000, 700 }, center = true,
})
hl.window_rule({
    name = "file-pickers",
    match = { class = "xdg-desktop-portal-gtk", title = "^(Open.*Files?|Save.*Files?|All Files|Save)" },
    float = true, center = true,
})
hl.window_rule({
    name = "obsidian-workspace",
    match = { class = ".*obsidian.*" },
    workspace = "3 silent",
})
hl.window_rule({
    name = "spotify-workspace",
    match = { class = ".*spotify.*" },
    workspace = "5 silent",
})
hl.window_rule({
    name = "webex",
    match = { class = "^(webex)$" },
    workspace = "special:im silent",
    float = true,
    no_initial_focus = true,
    suppress_event = "activate activatefocus",
    focus_on_activate = false,
})
hl.window_rule({
    name = "outlook-workspace",
    match = { initial_title = ".*Outlook.*" },
    workspace = "special:mail silent",
})

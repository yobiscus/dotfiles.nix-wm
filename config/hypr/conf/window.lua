local colors = require("colors-matugen")
local programs = require("conf.variables")

hl.config({
    general = {
        gaps_in = 10,
        gaps_out = 10,
        border_size = 2,
        col = {
            active_border = colors.primary,
            inactive_border = colors.on_primary,
        },
        layout = "master",
        resize_on_border = true,
    },
})

hl.workspace_rule({ workspace = "special:im", gaps_in = 10, gaps_out = 40, layout = "master" })
hl.workspace_rule({ workspace = "special:mail", gaps_in = 10, gaps_out = 40, layout = "master" })
hl.workspace_rule({ workspace = "special:term", gaps_in = 10, gaps_out = 40, layout = "master" })

hl.on("workspace.created", function(workspace)
    if workspace.addressable_name == "special:term" and workspace.is_empty then
        hl.exec_cmd(programs.terminal, { workspace = "special:term silent" })
    end
end)

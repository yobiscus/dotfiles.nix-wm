{ config, lib, pkgs, ... }:

{
  home.packages = [
    pkgs.fira-sans
    pkgs.font-awesome
    pkgs.material-icons
    pkgs.pavucontrol
  ];

  programs.waybar = {
    enable = true;
    package = pkgs.waybar.overrideAttrs (old: {
      # Backport https://github.com/Alexays/Waybar/pull/5013 until the next release.
      patches = (old.patches or []) ++ lib.optionals (old.version == "0.15.0") [
        (pkgs.fetchpatch {
          url = "https://github.com/Alexays/Waybar/commit/e17c0d9f0a73acc370df60ec8c532b1ed2385c73.patch";
          # Native workspace scrolling was added after 0.15.0; our scroll binds use Lua already.
          excludes = [ "src/modules/hyprland/workspaces.cpp" ];
          hash = "sha256-QsPcxs6B8YPIPE3IzBuxER+12Ur+3JoshouDm/3T3xE=";
        })
      ];
      postPatch = (old.postPatch or "") + lib.optionalString (old.version == "0.15.0") ''
        # Use the current Lua selector for the move-to-monitor click variant.
        substituteInPlace src/modules/hyprland/backend.cpp \
          --replace-fail 'monitor = \"current\"' 'on_current_monitor = true'
      '';
    });
  };

  home.file = {
    ".config/waybar/config.jsonc".source = ./config/waybar/config.jsonc;
    ".config/waybar/modules.json".source = ./config/waybar/modules.json;
    ".config/waybar/scripts/herdr-status.py" = {
      source = ./config/waybar/scripts/herdr-status.py;
      executable = true;
    };
    ".config/waybar/scripts/vpn-status.py" = {
      source = ./config/waybar/scripts/vpn-status.py;
      executable = true;
    };
    ".config/waybar/scripts/webex-unread.py" = {
      source = ./config/waybar/scripts/webex-unread.py;
      executable = true;
    };
    ".config/waybar/assets/tailscale.svg".source =
      ./config/waybar/assets/tailscale.svg;
    ".config/waybar/assets/cisco.svg".source =
      ./config/waybar/assets/cisco.svg;
    ".config/waybar/assets/pia.svg".source =
      ./config/waybar/assets/pia.svg;
    ".config/waybar/style.css".source = ./config/waybar/style.css;
    # colors.css is modified by Mutagen, so it has to be writable
    ".config/waybar/colors.css".source =
      config.lib.file.mkOutOfStoreSymlink
      "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/waybar/colors.css";
  };
}

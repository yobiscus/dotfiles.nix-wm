{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.fira-sans
    pkgs.font-awesome
    pkgs.material-icons
    pkgs.pavucontrol
    pkgs.python3
  ];

  programs.waybar = {
    enable = true;
  };

  home.file = {
    ".config/waybar/config.jsonc".source = ./config/waybar/config.jsonc;
    ".config/waybar/modules.json".source = ./config/waybar/modules.json;
    ".config/waybar/scripts/herdr-status.py" = {
      source = ./config/waybar/scripts/herdr-status.py;
      executable = true;
    };
    ".config/waybar/style.css".source = ./config/waybar/style.css;
    # colors.css is modified by Mutagen, so it has to be writable
    ".config/waybar/colors.css".source =
      config.lib.file.mkOutOfStoreSymlink
      "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/waybar/colors.css";
  };
}

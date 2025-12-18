{ config, pkgs, ... }:

{
  programs.waybar = {
    enable = true;
  };

  home.file.".config/waybar".source = ./config/waybar;
}

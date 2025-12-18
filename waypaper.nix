{ config, pkgs, lib, ... }:

{
  home.packages = [
    pkgs.hyprpaper
    pkgs.waypaper
  ];

  home.file.".config/waypaper".source = ./config/waypaper;
  home.file.".config/wallpapers".source = ./config/wallpapers;
}

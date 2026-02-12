{ config, pkgs, lib, ... }:

{
  home.packages = [
    pkgs.hyprpaper
  ];

  home.file.".config/hypr/hyprpaper.conf".source = ./config/hypr/hyprpaper.conf;
  home.file.".config/wallpapers".source = ./config/wallpapers;
}

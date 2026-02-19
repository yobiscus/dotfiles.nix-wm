{ config, pkgs, lib, ... }:

{
  home.packages = [
    pkgs.blueman
    pkgs.brightnessctl
    pkgs.hypridle
    pkgs.hyprshot
    pkgs.playerctl
    pkgs.wofi
  ];

  wayland.windowManager.hyprland = {
    enable = true;
    extraConfig = ''
      source = ~/.config/hypr/conf/main.conf
    '';
  };

  home.file.".config/hypr/conf".source = ./config/hypr/conf;
  home.file.".config/hypr/scripts".source = ./config/hypr/scripts;

  home.file.".config/hypr/colors-matugen.conf".source =
    config.lib.file.mkOutOfStoreSymlink
    "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/hypr/colors-matugen.conf";

  home.file.".config/hypr/hypridle.conf".source = ./config/hypr/hypridle.conf;
}

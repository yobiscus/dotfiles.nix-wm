{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.kitty
  ];

  home.file.".config/kitty/kitty.conf".source = ./config/kitty/kitty.conf;
  # colorsmatugen.conf is modified by Mutagen, so it has to be writable
  home.file.".config/kitty/colors-matugen.conf".source =
    config.lib.file.mkOutOfStoreSymlink
    "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/kitty/colors-matugen.conf";
}

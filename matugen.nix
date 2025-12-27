{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.matugen
  ];

  # home.file.".config/matugen".source = ./config/matugen;
  home.file.".config/matugen".source =
    config.lib.file.mkOutOfStoreSymlink
    "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/matugen";
}

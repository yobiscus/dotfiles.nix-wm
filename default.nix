{ config, pkgs, ... }:

{
  imports = [
    ./hyprland.nix
  ];

  home.packages = [
    pkgs.firefox
  ];

  home.pointerCursor = {
    gtk.enable = true;
    package = pkgs.bibata-cursors;
    name = "Bibata-Modern-Ice";
    size = 22;
  };
}

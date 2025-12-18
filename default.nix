{ config, pkgs, ... }:

{
  imports = [
    ./hyprland.nix
    ./kitty.nix
    ./waybar.nix
    ./waypaper.nix
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

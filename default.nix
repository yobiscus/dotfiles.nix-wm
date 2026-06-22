{ config, pkgs, ... }:

{
  imports = [
    ./hyprland.nix
    ./hyprlock.nix
    ./hyprpaper.nix
    ./firefox.nix
    ./kitty.nix
    ./matugen.nix
    ./swaync.nix
    ./waybar.nix
  ];

  home.packages = [
    pkgs.blueman
    pkgs.bluez
    pkgs.spotify
  ];

  home.pointerCursor = {
    gtk.enable = true;
    package = pkgs.bibata-cursors;
    name = "Bibata-Modern-Ice";
    size = 22;
  };

  services.ssh-agent = {
    enable = true;
  };
}

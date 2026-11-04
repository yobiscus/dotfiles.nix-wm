{ config, gome, pkgs, ... }:

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
    (pkgs.callPackage gome { })
    pkgs.blueman
    pkgs.bluez
    pkgs.gimp
    pkgs.spotify
  ];

  home.file.".config/wireplumber/main.lua.d/51-sof-headroom.lua" = {
    source = ./config/wireplumber/main.lua.d/51-sof-headroom.lua;
    onChange = ''
      ${config.systemd.user.systemctlPath} --user try-restart wireplumber.service
    '';
  };

  home.pointerCursor = {
    enable = true;
    gtk.enable = true;
    package = pkgs.bibata-cursors;
    name = "Bibata-Modern-Ice";
    size = 22;
  };

  services.ssh-agent = {
    enable = true;
  };
}

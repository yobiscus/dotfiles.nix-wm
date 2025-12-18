{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.fira-sans
    pkgs.font-awesome
    pkgs.material-icons
    pkgs.pavucontrol
  ];

  programs.waybar = {
    enable = true;
  };

  home.file.".config/waybar".source = ./config/waybar;
  # home.file.".config/waybar".source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/waybar";
}

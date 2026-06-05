{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.xdg-utils
    pkgs.firefoxpwa
  ];

  programs.firefox = {
    enable = true;
    configPath = "${config.xdg.configHome}/mozilla/firefox";
    nativeMessagingHosts = [ pkgs.firefoxpwa ];
  };

  xdg.enable = true;
}

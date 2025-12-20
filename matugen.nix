{ config, pkgs, ... }:

{
  home.packages = [
    pkgs.matugen
  ];

  home.file.".config/matugen".source = ./config/matugen;
}

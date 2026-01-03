{ config, pkgs, lib, ... }:

{
  home.packages = [
    pkgs.blueman
    pkgs.brightnessctl
    pkgs.hypridle
    pkgs.hyprshot
    pkgs.wofi
  ];

  wayland.windowManager.hyprland = {
    enable = true;
    extraConfig = ''
      source = ~/.config/hypr/conf/main.conf
    '';
  };

  programs.hyprlock = {
    enable = true;
    # Use system PAM. PAM installed by Nix isn't compatible with Ubuntu/Debian config.
    # https://github.com/hyprwm/hyprlock/issues/135#issuecomment-3380596630
    package = pkgs.writeShellScriptBin "hyprlock" ''
      set -euo pipefail
      # Use the Hyprlock binary that Nix built
      REAL="${pkgs.hyprlock}/bin/hyprlock"
      # Force it to run under Ubuntu's dynamic loader instead of Nix's
      LOADER="/lib64/ld-linux-x86-64.so.2"
      [ -x "$LOADER" ] || LOADER="/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
      # Tell the loader where to look for shared libraries first
      # These are Ubuntu's system lib dirs, so pam_unix & friends are found here
      export LD_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
      # Extra safety: preload system libpam.so explicitly, so we never use Nix's
      export LD_PRELOAD="/lib/x86_64-linux-gnu/libpam.so.0"
      # Finally, exec Hyprlock through the system loader with the correct libs
      exec "$LOADER" --library-path "$LD_LIBRARY_PATH" "$REAL" "$@"
    '';
    settings = {
      source = "colors-matugen.conf";
      general = {
        hide_cursor = true;
        ignore_empty_input = true;
      };
      animations = {
        enabled = true;
        fade_in = {
          duration = 300;
          bezier = "easeOutQuint";
        };
        fade_out = {
          duration = 300;
          bezier = "easeOutQuint";
        };
      };
      background = [
        {
          path = "$image";
        }
      ];
      input-field = [
        {
          monitor = "";
          size = "200, 50";
          position = "0, -80";
          dots_center = true;
          fade_on_empty = false;
          font_color = "rgb(202, 211, 245)";
          inner_color = "rgb(91, 96, 120)";
          outer_color = "rgb(24, 25, 38)";
          outline_thickness = 5;
          placeholder_text = "<span foreground=\"##cad3f5\">Password...</span>";
          shadow_passes = 2;
          fail_color = "$error";
        }
      ];
      label = [
        {
          monitor = "";
          # clock
          text = "cmd[update:1000] echo $TIME";
          color = "#ffffff";
          font_size = 70;
          position = "-50, 20";
          halign = "right";
          valign = "bottom";
          shadow_passes = 5;
          shadow_size = 10;
        }
        {
          monitor = "";
          text = "$USER";
          color = "#ffffff";
          font_size = 20;
          font_family = "JetBrainsMono Nerd Font";
          position = "-50, 120";
          halign = "right";
          valign = "bottom";
          shadow_passes = 5;
          shadow_size = 10;
        }
      ];
    };
  };

  home.file.".config/hypr/conf".source = ./config/hypr/conf;
  home.file.".config/hypr/scripts".source = ./config/hypr/scripts;

  home.file.".config/hypr/colors-mutagen.conf".source =
    config.lib.file.mkOutOfStoreSymlink
    "${config.home.homeDirectory}/.dotfiles/config/home-manager/modules/wm/config/hypr/colors-matugen.conf";

  home.file.".config/hypr/hypridle.conf".source = ./config/hypr/hypridle.conf;
}

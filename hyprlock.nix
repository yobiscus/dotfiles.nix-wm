{ config, pkgs, pam-shim, lib, ... }:

{
  # compatibility with non-Nix (maybe specifically Ubuntu) PAM
  pamShim.enable = true;

  programs.hyprlock = {
    enable = true;
    package = config.lib.pamShim.replacePam pkgs.hyprlock;
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
}

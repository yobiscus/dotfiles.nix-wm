{ config, pkgs, ... }:

{
  programs.kitty = {
    enable = true;
    settings = {
      shell = "${pkgs.zsh}/bin/zsh";
      font_family = "JetBrainsMono Nerd Font";
      font_size = 10.5;
      bold_font = "auto";
      italic_font = "auto";
      bold_italic_font = "auto";
      cursor_blink_interval = 0.5;
      cursor_stop_blinking_after = 1;
      scrollback_lines = 9999;
      enable_audio_bell = "no";
      window_padding_width = 8;
      hide_window_decorations = "yes";
      background_opacity = 0.7;
      dynamic_background_opacity = "yes";
      selection_foreground = "none";
      selection_background = "none";
      cursor_trail = 1;
    };
  };
}

{ pkgs, lib, config, inputs, ... }:
let
  pkgs-unstable = import inputs.nixpkgs-unstable { system = pkgs.stdenv.system; };
in
{
  # https://devenv.sh/basics/
  # env = {
  #   ARDUINO_DIRECTORIES_USER = "${config.devenv.root}/.arduino/user";
  #   ARDUINO_DIRECTORIES_DATA = "${config.devenv.root}/.arduino/data";
  # };
  # https://devenv.sh/packages/
  # packages = with pkgs-unstable; [
  #   arduino-cli
  #   zlib # wird von der xtensa-Toolchain benötigt
  #   just
  # ];

  languages.python = {
    enable = true;
    venv.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}

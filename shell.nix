{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.beautifulsoup4
    pkgs.python3Packages.requests
    pkgs.python3Packages.markdownify
    pkgs.python3Packages.rich
  ];
}
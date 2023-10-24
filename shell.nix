with import <nixpkgs> { };

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    python3Packages.pip

    python3Packages.requests
    python3Packages.beautifulsoup4
    python3Packages.lxml

    pre-commit
  ];

}

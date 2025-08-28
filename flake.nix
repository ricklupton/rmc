{
  description = "Nix flakes";

  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = { url = "github:nix-community/poetry2nix"; };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system: 
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
          mkPoetryEnv mkPoetryApplication defaultPoetryOverrides;
        poetryArgs = {
          python = pkgs.python312;
          projectDir = ./.;
          preferWheels = true;
          overrides = defaultPoetryOverrides.extend (final: prev: {
            click = prev.click.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.flit-scm ];
            });
            rmc = prev.rmc.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ];
            });
          });
        };
        pythonEnv = mkPoetryEnv (poetryArgs);
        rmcBin = mkPoetryApplication (poetryArgs);
      in
      {
        packages = {
          default = rmcBin;
        };
        devShells.default = pkgs.mkShell {
          buildInputs = [
	        pkgs.poetry
	        rmcBin
	        pythonEnv
          ];
        };
      });
}

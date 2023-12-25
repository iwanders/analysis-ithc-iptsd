{
  inputs = {
    nixpkgs.url = "nixpkgs/ffcadd021d929dd87dcc3a3fc39098e13cbc8f60"; 
    flake-utils.url = "github:numtide/flake-utils/v1.0.0";
  };

  description = "";

  outputs = { self, nixpkgs, flake-utils }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = nixpkgs.legacyPackages.${system}.python3.withPackages(ps: with ps; [ numpy matplotlib ]);
    in {
      defaultPackage = pythonEnv; # If you want to juist build the environment
      devShell = pythonEnv.env; # We need .env in order to use `nix develop`
    });
}

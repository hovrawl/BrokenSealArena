# Broken Seal Arena

A Golden Sun: The Broken Seal romhack that turns the game into a team-versus-team
arena. It is a patch series over
[PascalPixel/alchemy](https://github.com/PascalPixel/alchemy), not a fork.

- `patches/`: the romhack, one patch per change (`git am` order).
- `UPSTREAM_BASE`: the upstream commit the patches apply to.
- `docs/CHANGES.md`: what each change does, how to build, and how to rebase onto
  newer upstream or The Lost Age.
- `scripts/`: `setup.sh` (WSL, from scratch) and `export-patches.ps1`.
- `build.ps1`: build and copy the ROM to `build\tbs-en.gba`.

`rom/` (your cartridge dump) and `build/` are never committed.

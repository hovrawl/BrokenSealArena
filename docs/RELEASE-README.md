# Broken Seal Arena (alpha)

A battle-arena romhack of **Golden Sun: The Broken Seal**. The game becomes a
team-versus-team arena: you pick a party in the lobby, fight CPU teams up a
ladder of cups (with Boss Rush, side cups and a mechanics teacher), and spend your
winnings in a party manager with stat, Djinn, Psynergy and item shops. Trophies for
the cups you clear stand in the lobby, and the Pause menu saves your series. Linked
battles are four a side. Everything is built to look like the game's own menus.

This is an **alpha**: it is playable but unfinished, English only, and it will
change. It builds from the source of a decompilation, so **there is no ROM in this
package and none is needed to build it.** You get a ROM by building it yourself.

## What is in this package

Not a game: the recipe. The romhack is a series of source patches
(`patches/tbs/`) over the decompilation of Golden Sun: The Broken Seal, and the
scripts (`scripts/`) that fetch that decompilation, apply the patches and build.

## How to build

Read `docs/BUILDING.md`. In short, on Linux, macOS or Windows with WSL:

```bash
sudo apt install build-essential git curl patch binutils-arm-none-eabi pkg-config \
  libpng-dev libutf8proc-dev python3 python3-pil
bash scripts/build.sh          # on Windows: .\build.ps1
```

The first build downloads and compiles old compilers (about 500 MB, and it takes
a long time); later builds are quick. The result is `build/tbs-en.gba`. Linux
(Ubuntu under WSL) is the tested path; macOS is untested.

## Credits

This project stands on two bases, and could not exist without them:

- **Golden Sun Reloaded**, the rebalance of The Broken Seal from the Golden Sun
  Hacking Community forum (forum.goldensunhacking.net, topic 2779). Its rules and
  data are ported into this hack.
- **alchemy** ([PascalPixel/alchemy](https://github.com/PascalPixel/alchemy)), the
  matching decompilation of The Broken Seal that this is built on. The patches here
  apply to it at the commit named in `UPSTREAM`.

Golden Sun is a trademark of Nintendo and Camelot. This is a fan project and is not
affiliated with them.

## Please don't share built ROMs

Build it for yourself, from your own copy of this package. Do not share the ROMs it
produces, or any save or asset extracted from them.

This build: commit @COMMIT@.

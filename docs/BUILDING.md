# Building Broken Seal Arena

The project is a patch series over the decompilation
[PascalPixel/alchemy](https://github.com/PascalPixel/alchemy). Building it means:
get upstream at the commit this repo pins, apply our patches, build the old
compilers once, and run `make`. `scripts/build.sh` does all of that; this page
also gives the raw commands, so you can build without our scripts.

- **No ROM is needed.** Upstream builds The Broken Seal entirely from source:
  the pictures, music and text come with it. (Only a future Lost Age port would
  want your own dump, as `roms/tla-en.gba`. An optional dump in `roms/` is
  ignored today.)
- **The first build compiles the old compilers** the game was matched with
  (GCC 2.95.2 and others). It downloads their sources from ftp.gnu.org, prints
  many old-compiler warnings (normal), needs about 500 MB, and takes a long time.
  It happens once; later builds take a few minutes.
- The result is `build/tbs-en.gba`. Please don't share built ROMs.
- **Linux (Ubuntu under WSL) is the tested path.** macOS is best effort and
  **untested**: upstream says it builds there, we have not tried it.

## The short way

```bash
git clone <this repo>     # or unzip the release zip
cd BrokenSealArena
bash scripts/build.sh
```

`bash scripts/build.sh --help` lists the options. The work directory (the clone of
upstream) is, in order: `--work-dir DIR`, `$ALCHEMY_DIR`, the first line of a
file named `.alchemy-dir` in the repo root (git-ignored), or `work/alchemy` in
the repo. If it is empty or missing, the script clones upstream at the pinned
commit and applies `patches/tbs/*.patch` with `git am`. If it already is a git
clone (a developer's, with the patches as commits) it is built as it is.

## 1. Install the tools

These are upstream's packages (see its `INSTALL.md`), plus Python with Pillow for
two sprite generators.

**Linux** (Debian or Ubuntu):

```bash
sudo apt install build-essential git curl patch binutils-arm-none-eabi \
  pkg-config libpng-dev libutf8proc-dev python3 python3-pil
```

**macOS** (with [Homebrew](https://brew.sh)), untested:

```bash
xcode-select --install
brew install arm-none-eabi-binutils pkg-config libpng utf8proc python
python3 -m pip install pillow
```

**Windows:** use WSL. In PowerShell run `wsl --install`, restart, open
**Ubuntu**, install the Linux packages above inside it, then see below.

## 2. The raw commands

`<PINNED>` and `<URL>` are in the file `UPSTREAM` of the release zip, or in the
git repo: `git ls-files -s alchemy` (the commit) and `.gitmodules` (the URL).
Use a folder whose path has no spaces, on the Linux file system.

```bash
git clone <URL> alchemy
cd alchemy
git checkout -b arena <PINNED>
git submodule update --init --recursive alchemy-gcc
git config user.name "you"; git config user.email "you@example.com"   # git am needs them
git am --3way /path/to/BrokenSealArena/patches/tbs/*.patch

make -j"$(nproc)" bootstrap        # once: the old compilers, long (see above)

# The sprite sheets are derived from the game's art and are not in git:
python3 /path/to/BrokenSealArena/scripts/gen-opponent-sprites.py games/tbs/src/graphics/sprite
python3 /path/to/BrokenSealArena/scripts/gen-trophy-sprites.py   games/tbs/src/graphics/sprite

make -j"$(nproc)" tbs-en ROM_END_tbs=0x08806000     # ROM_END: see ROM_END in scripts/build.sh
```

On macOS use `$(sysctl -n hw.ncpu)` for `nproc`. The ROM is
`out/tbs-en/tbs-en.gba`. The cup files (`arena_cups.c` and friends) are already
inside the patches; `scripts/gen-cups.py` only matters to someone changing
`scripts/cupdata.py`.

## Windows with WSL, and `build.ps1`

From PowerShell in the repo folder:

```powershell
.\build.ps1                          # work directory: ~/brokenseal-arena/alchemy in WSL
.\build.ps1 -WorkDir '~/alchemy'     # a path inside WSL
.\build.ps1 -Distro Ubuntu           # not your default distribution
```

It calls `scripts/build.sh` through `wsl` and leaves the ROM in
`build\tbs-en.gba` (or `build\tbs-en.new.gba` when an emulator holds the first
open). **The work directory is inside the WSL home on purpose:** building on a
Windows drive (`/mnt/c/...`) is far too slow and breaks file modes. If a file
`.alchemy-dir` exists in the repo root, that is used instead of the default.

## Troubleshooting

- **Check the build log, not an exit code.** A failed `make` through `wsl` can
  still print 0. Look for `***` in the log and that `out/tbs-en/tbs-en.gba` has a
  fresh timestamp.
- **`png.h`, `utf8proc.h` or `arm-none-eabi-as` not found:** a package from step 1
  is missing.
- **`alchemy-gcc` is empty:** run `git submodule update --init --recursive alchemy-gcc`
  in the work directory, then `make bootstrap`.
- **"No rule to make target ... needed by out/tbs-en/deps.mk":** after switching the
  work directory to a tree with different sources, delete `out/tbs-en/deps.mk` and
  `out/tbs-en/objects.mk`; make rebuilds them.
- **`ModuleNotFoundError: PIL`:** install Pillow (`python3-pil`, or `pip install pillow`).
- **Slow build, CRLF or file-mode errors on WSL:** the work directory is on `/mnt/c`.
  Use one inside the WSL home.
- **Odd path errors:** use a work directory whose path has no spaces.
- **`git am` stops:** the pinned commit was not checked out (patches apply only
  to it), or `user.name`/`user.email` are not set in the clone.
- **The emulator holds `tbs-en.gba` open:** the Windows wrapper writes `tbs-en.new.gba`.

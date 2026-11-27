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
  (GCC 2.95.2 and others), from sources upstream vendors. It prints many
  old-compiler warnings (normal), needs about 500 MB, and takes a long time.
  It happens once; later builds take a few minutes.
- The result is `build/tbs-en.gba`. Please don't share built ROMs.
- **Windows (with MSYS2) and Linux are tested** and give the same ROM, byte for
  byte. macOS is best effort and **untested**: upstream says it builds there,
  we have not tried it. Windows needs no WSL (WSL still works: it is Linux).
- There is also a **desktop build** of the game (patch 0046, a 32-bit program
  for Windows or Linux): see "The desktop build" below.

## The short way

```bash
git clone <this repo>     # or unzip the release zip
cd BrokenSealArena
bash scripts/build.sh     # on Windows: .\build.ps1 from PowerShell
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

**Windows**, with [MSYS2](https://www.msys2.org) (a native Windows bash with
make and GCC). From PowerShell:

```powershell
winget install MSYS2.MSYS2
C:\msys64\usr\bin\bash.exe -lc "pacman -Syu --noconfirm"
C:\msys64\usr\bin\bash.exe -lc "pacman -S --needed --noconfirm base-devel git gcc python mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-arm-none-eabi-binutils mingw-w64-ucrt-x86_64-libpng mingw-w64-ucrt-x86_64-libutf8proc mingw-w64-ucrt-x86_64-pkgconf mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pillow"
```

Run the `-Syu` line again if it asks for a restart. For the desktop build add
`mingw-w64-i686-gcc mingw-w64-i686-binutils`; for the smoke tests
(docs/TESTING.md) add `mingw-w64-ucrt-x86_64-mgba`. Then see "Windows and
`build.ps1`" below.

Turn on Windows **Developer Mode** (Settings, System, For developers), or run
the first build from an administrator shell: upstream's compiler sources hold
two symbolic links, and Windows lets a normal user make links only in
Developer Mode.

## 2. The raw commands

`<PINNED>` and `<URL>` are in the file `UPSTREAM` of the release zip, or in the
git repo: `git ls-files -s alchemy` (the commit) and `.gitmodules` (the URL).
Use a folder whose path has no spaces (under WSL, on the Linux file system).
These are the Linux and macOS commands; on Windows `make` also needs the
settings in `scripts/msys2/env.sh` ("How the Windows build works" below), so
use `scripts/build.sh` there.

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

## Windows and `build.ps1`

From PowerShell in the repo folder:

```powershell
.\build.ps1                           # the ROM: build\tbs-en.gba
.\build.ps1 -WorkDir D:\src\alchemy   # another work directory
.\build.ps1 -Native                   # the desktop build: build\native\tbs-native.exe
.\build.ps1 -Native -Headless         # the smoke-test build: build\native-headless\
```

It runs `scripts/build.sh` (or `scripts/build-native.sh`) in MSYS2's bash, from
`C:\msys64` (or `$env:MSYS2_ROOT`). The work directory defaults to
`work\alchemy` in the repo, or the first line of `.alchemy-dir` (a Windows
path, or one relative to the repo). The ROM is in `build\tbs-en.gba` (or
`build\tbs-en.new.gba` when an emulator holds the first open). A first build
clones upstream, applies the patches and builds the old compilers: count on
half an hour. Later builds take a few minutes.

### How the Windows build works

Upstream's build is GNU make with Unix shell recipes, and `make bootstrap`
compiles 2000-era compilers whose sources assume a POSIX system. MSYS2 has
both, as Windows programs. Nothing in upstream is changed:
`scripts/msys2/env.sh` sets make variables and PATH so that

- upstream's host tools (`tools/ags-*`) are built by UCRT64's GCC, with
  `scripts/msys2/compat.h` force-included (`mkdir` without a mode, and a
  `rename` that replaces its target as POSIX's does) and binary-mode stdio.
  Each also gets a copy without `.exe`, the name make looks for;
- the matched compilers are built by MSYS's own GCC (its POSIX layer), with
  `scripts/msys2/include/stab.h` (GCC's own copy) and libiberty told that the
  system has `sys_errlist`;
- `scripts/msys2/bin/sha256sum` prints the Linux listing format, which
  upstream's source checks hash;
- git keeps symbolic links and LF line ends in the work directory.

## The desktop build

Patch 0046 compiles the game's C for a PC (`port/` in the work directory; its
`README.md` explains how). It is 32-bit, has no sound yet, and battle effects
do not draw. Build the ROM first (the desktop build reads its lists), then:

- **Windows:** `.\build.ps1 -Native`. The window needs SDL3: download
  `SDL3-devel-<version>-mingw.zip` from
  [SDL's releases](https://github.com/libsdl-org/SDL/releases) and unpack it
  under `work\` (or set `SDL3_DIR` to its `i686-w64-mingw32` folder).
  `SDL3.dll` is copied beside `tbs-native.exe`; the program runs on its own,
  without MSYS2. `-Headless` needs no SDL.
- **Linux:** `bash scripts/build-native.sh [--headless]`, with `gcc-multilib`
  and, for the window, a 32-bit SDL3 (`sudo dpkg --add-architecture i386`,
  then `sudo apt install libsdl3-dev:i386`).

Keys: arrows, X (A), Z (B), Enter (Start), Backspace (Select), A and S (L and
R); hold Tab to fast-forward; Escape quits. A gamepad works too. The save is
`tbs-native.sav` in the folder you run it from.

## Troubleshooting

- **Check the build log, not an exit code.** A failed `make` run from another
  shell (`wsl`, or PowerShell into MSYS2) can still report 0. Look for `***` in
  the log and that `out/tbs-en/tbs-en.gba` has a fresh timestamp.
- **`png.h`, `utf8proc.h` or `arm-none-eabi-as` not found:** a package from step 1
  is missing.
- **`alchemy-gcc` is empty:** run `git submodule update --init --recursive alchemy-gcc`
  in the work directory, then `make bootstrap`.
- **"No rule to make target ... needed by out/tbs-en/deps.mk":** after switching the
  work directory to a tree with different sources, delete `out/tbs-en/deps.mk` and
  `out/tbs-en/objects.mk`; make rebuilds them.
- **`ModuleNotFoundError: PIL`:** install Pillow (`python3-pil`, or `pip install pillow`).
- **Slow build, CRLF or file-mode errors on WSL:** the work directory is on `/mnt/c`.
  Use one inside the WSL home, or build with MSYS2 instead.
- **Windows: `agbcc differs from pret/agbcc`:** the two symbolic links in
  `alchemy-gcc/agbcc/gcc_arm` were checked out as text files (no Developer
  Mode). Turn it on; then, in `alchemy-gcc`, run `git config core.symlinks true`,
  delete `agbcc/gcc_arm/obstack.c` and `agbcc/gcc_arm/splay-tree.c`, and
  `git checkout` them again.
- **Windows: a tool says "write failed", or make finds "No rule" for an asset:**
  the tools were built without `scripts/msys2/env.sh`'s settings. Delete
  `tools/out/ags-*` in the work directory and build again.
- **Odd path errors:** use a work directory whose path has no spaces.
- **`git am` stops:** the pinned commit was not checked out (patches apply only
  to it), or `user.name`/`user.email` are not set in the clone.
- **The emulator holds `tbs-en.gba` open:** the Windows wrapper writes `tbs-en.new.gba`.

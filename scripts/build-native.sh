#!/usr/bin/env bash
# Builds the native (desktop) version of the game, patch 0046's port/ in the
# work directory, and copies it to build/native/ (or build/native-headless/).
# Build the ROM first (scripts/build.sh): the native build reads its asset,
# text and object lists.
#
#   scripts/build-native.sh [--headless] [--work-dir DIR] [--help]
#
# --headless  no window: runs smoke scripts (scripts/smoke/*.txt) and writes
#             PNG shots (tbs-native --script FILE --shots DIR).
#
# Linux: needs gcc-multilib, and for the window a 32-bit SDL3 that pkg-config
# finds (Debian/Ubuntu: libsdl3-dev:i386; the script points pkg-config at the
# i386 directory).
# Windows: runs in MSYS2 (build.ps1 -Native runs it there) with the MINGW32
# compiler, a 32-bit Windows build. For the window it needs SDL's MinGW
# developer package (SDL3-devel-*-mingw), unpacked under work/; or set SDL3_DIR
# to its i686-w64-mingw32 directory. SDL3.dll is copied beside the program.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=alchemy-dir.sh
. "$HERE/alchemy-dir.sh"

HEADLESS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --headless) HEADLESS=1; shift ;;
    --work-dir) [ $# -ge 2 ] || { echo "--work-dir needs a directory" >&2; exit 2; }
                ALCHEMY_DIR="$2"; export ALCHEMY_DIR; shift 2 ;;
    -h|--help) sed -n '2,/^set -e/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

WORK="$(bsa_alchemy_dir)"
JOBS="$(nproc 2>/dev/null || echo 2)"
[ -f "$WORK/out/tbs-en/objects.mk" ] || { echo "Build the ROM first (scripts/build.sh): $WORK/out/tbs-en/objects.mk is missing." >&2; exit 1; }

NAME=native; [ "$HEADLESS" = 1 ] && NAME=native-headless
DEST="$ROOT/build/$NAME"
VARS=(HEADLESS="$HEADLESS")
DLL=

case "$(uname -s)" in
  MINGW*|MSYS*|UCRT*|CLANG*)
    # The 32-bit MinGW compiler and binutils first; arm-none-eabi-nm (for the
    # GBA build's symbols) is UCRT64's.
    export PATH="/mingw32/bin:/usr/bin:/ucrt64/bin:$PATH"
    command -v i686-w64-mingw32-gcc >/dev/null || {
      echo "No 32-bit MinGW compiler: pacman -S mingw-w64-i686-gcc mingw-w64-i686-binutils (docs/BUILDING.md)" >&2; exit 1; }
    VARS+=(CC=i686-w64-mingw32-gcc)
    if [ "$HEADLESS" = 0 ]; then
      SDL="${SDL3_DIR:-}"
      if [ -z "$SDL" ]; then
        SDL="$(ls -d "$ROOT"/work/SDL3-*/i686-w64-mingw32 2>/dev/null | sort -V | tail -n 1 || true)"
      fi
      [ -n "$SDL" ] && [ -f "$SDL/include/SDL3/SDL.h" ] || {
        echo "No 32-bit SDL3: unpack SDL3-devel-<version>-mingw.zip (github.com/libsdl-org/SDL/releases) under $ROOT/work/, or set SDL3_DIR (docs/BUILDING.md)." >&2; exit 1; }
      # SDL3.dll is delay-loaded: at start-up the program then loads only
      # system DLLs, as the headless one does, and maps the GBA's regions
      # before SDL and the libraries it pulls in (user32, gdi32 and the rest)
      # can take their addresses (seen: a mapped view over 0x02000000).
      DELAY="$WORK/out/sdl3-delay"
      if [ ! -f "$DELAY/libSDL3_delay.a" ] || [ "$SDL/bin/SDL3.dll" -nt "$DELAY/libSDL3_delay.a" ]; then
        mkdir -p "$DELAY"
        { echo "LIBRARY SDL3.dll"; echo "EXPORTS"
          objdump -p "$SDL/bin/SDL3.dll" | awk '/\[Ordinal\/Name Pointer\] Table/ {on = 1; next}
            on && /^[[:space:]]*\[ *[0-9]+\]/ {print $NF; next} on && NF == 0 {on = 0}'
        } > "$DELAY/SDL3.def"
        dlltool --input-def "$DELAY/SDL3.def" --dllname SDL3.dll --output-delaylib "$DELAY/libSDL3_delay.a"
      fi
      VARS+=("SDL_CFLAGS=-I$SDL/include" "SDL_LIBS=-L$DELAY -lSDL3_delay -ldelayimp")
      DLL="$SDL/bin/SDL3.dll"
    fi
    ;;
  *)
    if [ "$HEADLESS" = 0 ] && [ -d /usr/lib/i386-linux-gnu/pkgconfig ]; then
      export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig"
    fi
    ;;
esac

make -C "$WORK" -f port/Makefile -j"$JOBS" "${VARS[@]}"

BIN="$WORK/out/native-tbs-en"
[ "$HEADLESS" = 0 ] || BIN="$BIN-headless"
mkdir -p "$DEST"
if [ -f "$BIN/tbs-native.exe" ]; then
  cp "$BIN/tbs-native.exe" "$DEST/"
else
  cp "$BIN/tbs-native" "$DEST/"
fi
[ -z "$DLL" ] || cp "$DLL" "$DEST/"
printf '\n== Done: %s\n' "$DEST"

#!/usr/bin/env bash
# Builds Broken Seal Arena (English) and leaves the ROM in build/tbs-en.gba.
# Works on Linux, macOS and inside WSL. See docs/BUILDING.md.
#
#   scripts/build.sh [--work-dir DIR] [--verify] [--help]
#
# The work directory holds the clone of upstream (PascalPixel/alchemy). It is,
# in order: --work-dir, $ALCHEMY_DIR, the first line of the file .alchemy-dir in
# the repo root, or <repo>/work/alchemy. (Under WSL do not use a folder on /mnt/c:
# it is far too slow and breaks file modes. build.ps1 picks one in your WSL home.)
#
#   * If the work directory is not there yet (or empty), it is cloned from
#     upstream at the commit this repo pins, and patches/tbs/*.patch are applied
#     with git am, on a branch called arena.
#   * If it already is a git clone (the developer's own, with the patches as
#     commits), it is built as it is; its commits are not touched.
#   * make bootstrap runs once, if the old compilers are not built yet.
#   * The sprite sheets that are not kept in git are generated, then make runs.
#
# --verify also runs upstream's compare (only passes for unmodified source).
# No ROM is needed to build The Broken Seal: upstream builds it from source.
# (Only The Lost Age would want a dump, as roms/tla-en.gba.)
set -euo pipefail

# The one place the ROM's end address is set. main.ld moves the last region on
# by 0x5000 to make room for the added data, and the image is padded to match.
ROM_END=0x08806000

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=alchemy-dir.sh
. "$HERE/alchemy-dir.sh"

VERIFY=
while [ $# -gt 0 ]; do
  case "$1" in
    --work-dir) [ $# -ge 2 ] || { echo "--work-dir needs a directory" >&2; exit 2; }
                ALCHEMY_DIR="$2"; export ALCHEMY_DIR; shift 2 ;;
    --verify) VERIFY=1; shift ;;
    -h|--help) sed -n '2,/^set -e/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//' ; exit 0 ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

WORK="$(bsa_alchemy_dir)"
JOBS="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)"
say() { printf '\n== %s\n' "$*"; }

case "$WORK" in
  /mnt/[a-z]/*) echo "Warning: $WORK is on a Windows drive; builds there are very slow and break file modes." >&2 ;;
esac

# The upstream commit and URL: UPSTREAM (in a release zip) or the git submodule pin.
if [ -f "$ROOT/UPSTREAM" ]; then
  BASE="$(sed -n 's/^commit[ =]*//p' "$ROOT/UPSTREAM" | head -n 1)"
  URL="$(sed -n 's/^url[ =]*//p' "$ROOT/UPSTREAM" | head -n 1)"
else
  BASE="$(git -C "$ROOT" ls-files -s alchemy | awk '{print $2}')"
  URL="$(git -C "$ROOT" config -f .gitmodules submodule.alchemy.url)"
fi

if ! git -C "$WORK" rev-parse --git-dir >/dev/null 2>&1; then
  if [ -e "$WORK" ] && [ -n "$(ls -A "$WORK" 2>/dev/null)" ]; then
    echo "$WORK exists but is not a git clone of upstream; choose another folder." >&2
    exit 1
  fi
  [ -n "$BASE" ] && [ -n "$URL" ] || { echo "Cannot tell which upstream commit to use (no UPSTREAM file, no submodule pin)." >&2; exit 1; }
  say "Cloning upstream $URL at ${BASE:0:10} into $WORK"
  mkdir -p "$(dirname "$WORK")"
  git clone "$URL" "$WORK"
  git -C "$WORK" checkout -q -b arena "$BASE"
  git -C "$WORK" submodule update --init --recursive alchemy-gcc
  git -C "$WORK" config user.name "$(git config --global user.name || echo romhack)"
  git -C "$WORK" config user.email "$(git config --global user.email || echo romhack@localhost)"
  say "Applying the patches"
  PATCHES=("$ROOT"/patches/tbs/*.patch)
  [ -e "${PATCHES[0]}" ] || { echo "No patches in $ROOT/patches/tbs" >&2; exit 1; }
  git -C "$WORK" am --3way "${PATCHES[@]}"
else
  say "Using the existing clone $WORK (branch $(git -C "$WORK" branch --show-current)); its commits are left alone"
fi

if [ ! -d "$WORK/tools/out/compilers" ]; then
  say "make bootstrap (first build only)"
  cat <<'MSG'
This builds the old compilers the game was matched with (GCC 2.95.2 and others).
It downloads their sources from ftp.gnu.org, prints many old-compiler warnings
(normal), needs about 500 MB, and takes a long time (tens of minutes). It runs
once; later builds skip it.
MSG
  make -C "$WORK" -j"$JOBS" bootstrap
fi

say "Generating the sprite sheets (git-ignored, derived from the game's art)"
SPRITES="$WORK/games/tbs/src/graphics/sprite"
python3 "$HERE/gen-opponent-sprites.py" "$SPRITES"
python3 "$HERE/gen-trophy-sprites.py" "$SPRITES"

say "make tbs-en ROM_END_tbs=$ROM_END"
make -C "$WORK" -j"$JOBS" tbs-en ROM_END_tbs="$ROM_END"
[ -z "$VERIFY" ] || make -C "$WORK" compare-tbs-en

mkdir -p "$ROOT/build"
if cp "$WORK/out/tbs-en/tbs-en.gba" "$ROOT/build/tbs-en.gba" 2>/dev/null; then
  rm -f "$ROOT/build/tbs-en.new.gba"
  say "Done: $ROOT/build/tbs-en.gba"
else
  # An emulator holding the ROM open locks it; leave that copy alone.
  cp "$WORK/out/tbs-en/tbs-en.gba" "$ROOT/build/tbs-en.new.gba"
  say "ROM is in use; wrote $ROOT/build/tbs-en.new.gba instead"
fi

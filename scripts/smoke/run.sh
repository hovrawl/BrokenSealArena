#!/usr/bin/env bash
# Runs one smoke script (Linux, or MSYS2 on Windows): run.sh SCRIPT [fresh]
# Builds the driver if needed, runs it against out/tbs-en/tbs-en.gba of the alchemy work directory,
# and leaves the screenshots in $T/shots, with a sheet.png of all of them.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../alchemy-dir.sh"
. "$HERE/env.sh"
ROM="$(bsa_alchemy_dir)/out/tbs-en/tbs-en.gba"
SCRIPT="$1"
mkdir -p ~/smoke $T/shots $T/smokesave
rm -f $T/shots/*
if [ "$2" = "fresh" ]; then rm -f $T/smokesave/*; fi
if [ ! -x ~/smoke/smoke ] || [ "$HERE/smoke.c" -nt ~/smoke/smoke ]; then
  "$SMOKE_CC" -O2 -o ~/smoke/smoke "$HERE/smoke.c" -lmgba -lpng
fi
smoke_own_dlls ~/smoke/smoke.exe
cd ~/smoke
./smoke "$ROM" "$HERE/$SCRIPT" $T/smokesave 2>$T/smoke.err | grep -v '^GBA ' || true
shots=$(ls $T/shots/*.png 2>/dev/null || true)
if [ -n "$shots" ]; then "$PYTHON" "$HERE/sheet.py" $T/shots/sheet.png $shots; fi

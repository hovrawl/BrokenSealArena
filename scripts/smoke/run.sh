#!/usr/bin/env bash
# Runs one smoke script in WSL: run.sh SCRIPT [fresh]
# Builds the driver if needed, runs it against out/tbs-en/tbs-en.gba of the alchemy work directory,
# and leaves the screenshots in /tmp/shots, with a sheet.png of all of them.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../alchemy-dir.sh"
ROM="$(bsa_alchemy_dir)/out/tbs-en/tbs-en.gba"
SCRIPT="$1"
mkdir -p ~/smoke /tmp/shots /tmp/smokesave
rm -f /tmp/shots/*
if [ "$2" = "fresh" ]; then rm -f /tmp/smokesave/*; fi
if [ ! -x ~/smoke/smoke ] || [ "$HERE/smoke.c" -nt ~/smoke/smoke ]; then
  gcc -O2 -o ~/smoke/smoke "$HERE/smoke.c" -lmgba -lpng
fi
cd ~/smoke
./smoke "$ROM" "$HERE/$SCRIPT" /tmp/smokesave 2>/tmp/smoke.err | grep -v '^GBA ' || true
shots=$(ls /tmp/shots/*.png 2>/dev/null || true)
if [ -n "$shots" ]; then python3 "$HERE/sheet.py" /tmp/shots/sheet.png $shots; fi

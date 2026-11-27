#!/usr/bin/env bash
# Runs a two-console link script (Linux, or MSYS2 on Windows): link.sh SCRIPT0 SCRIPT1
# Builds the link driver if needed and runs it against out/tbs-en/tbs-en.gba of the alchemy work directory.
# Shots go to $T/shots (name them p0_*.png and p1_*.png in the scripts).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../alchemy-dir.sh"
. "$HERE/env.sh"
ROM="$(bsa_alchemy_dir)/out/tbs-en/tbs-en.gba"
mkdir -p ~/smoke $T/shots $T/linksave
rm -f $T/shots/*
rm -f $T/linksave/*
if [ ! -x ~/smoke/link ] || [ "$HERE/link.c" -nt ~/smoke/link ]; then
  "$SMOKE_CC" -O2 -DENABLE_SCRIPTING -o ~/smoke/link "$HERE/link.c" -lmgba -lpng -lpthread
fi
smoke_own_dlls ~/smoke/link.exe
cd ~/smoke
./link "$ROM" "$HERE/$1" "$HERE/$2" $T/linksave 2>$T/link.err | grep -v '^GBA ' || true
cat $T/link.err | tail -5
shots=$(ls $T/shots/*.png 2>/dev/null || true)
if [ -n "$shots" ]; then "$PYTHON" "$HERE/sheet.py" $T/shots/sheet.png $shots; fi

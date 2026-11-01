#!/usr/bin/env bash
# Runs a two-console link script in WSL: link.sh SCRIPT0 SCRIPT1
# Builds the link driver if needed and runs it against out/tbs-en/tbs-en.gba of the alchemy work directory.
# Shots go to /tmp/shots (name them p0_*.png and p1_*.png in the scripts).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../alchemy-dir.sh"
ROM="$(bsa_alchemy_dir)/out/tbs-en/tbs-en.gba"
mkdir -p ~/smoke /tmp/shots /tmp/linksave
rm -f /tmp/shots/*
rm -f /tmp/linksave/*
if [ ! -x ~/smoke/link ] || [ "$HERE/link.c" -nt ~/smoke/link ]; then
  gcc -O2 -DENABLE_SCRIPTING -o ~/smoke/link "$HERE/link.c" -lmgba -lpng -lpthread
fi
cd ~/smoke
./link "$ROM" "$HERE/$1" "$HERE/$2" /tmp/linksave 2>/tmp/link.err | grep -v '^GBA ' || true
cat /tmp/link.err | tail -5
shots=$(ls /tmp/shots/*.png 2>/dev/null || true)
if [ -n "$shots" ]; then python3 "$HERE/sheet.py" /tmp/shots/sheet.png $shots; fi

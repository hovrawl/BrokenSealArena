#!/usr/bin/env bash
# Runs a two-console link script pair and keeps what is needed to read the result:
#   link-run.sh NAME   (runs link_NAME_0.txt and link_NAME_1.txt)
# Output: /tmp/NAME_out.txt (the driver's log), the shots copied to
# build/smoke/link/NAME/ (player 0's, plus a sheet.png of them).
# Set ROM1 to a second ROM to link two different builds (see link.c).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$1"
"$HERE/link.sh" "link_${NAME}_0.txt" "link_${NAME}_1.txt" > "/tmp/${NAME}_out.txt" 2>&1 || true
OUT="$HERE/../../build/smoke/link/$NAME"
rm -rf "$OUT"
mkdir -p "$OUT"
cp /tmp/shots/*.png "$OUT/" 2>/dev/null || true
tail -3 "/tmp/${NAME}_out.txt"

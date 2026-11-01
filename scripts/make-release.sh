#!/usr/bin/env bash
# Builds dist/BrokenSealArena-alpha.zip: the patches, the build scripts and the
# docs for building. No ROM, no built file, no images or other assets: the script
# checks that and fails if the zip holds any. Run from anywhere:
#   scripts/make-release.sh
# Needs git and python3. Works in a checkout without the submodule.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=BrokenSealArena-alpha
DIST="$ROOT/dist"
STAGE="$DIST/stage/$NAME"
ZIP="$DIST/$NAME.zip"
cd "$ROOT"

# The pinned upstream commit, from the submodule pointer (no checkout needed).
BASE="$(git ls-tree HEAD alchemy | awk '{print $3}')"
URL="$(git config -f .gitmodules submodule.alchemy.url)"
[ -n "$BASE" ] && [ -n "$URL" ] || { echo "No alchemy submodule pointer in HEAD" >&2; exit 1; }
COMMIT="$(git rev-parse --short HEAD)"

rm -rf "$DIST/stage" "$ZIP"
mkdir -p "$STAGE"

# Tools that read the Reloaded authors' own files are left out.
EXCLUDE='^scripts/(smoke/|__pycache__/)|\.pyc$|^scripts/(ips-[a-z-]+\.py|forum-text\.py|port-reloaded-tables\.py|table-check\.py|workbook-check\.py|xlsx-overview\.py|levelup-check\.py)$'
{
  git ls-files patches/tbs scripts | grep -Ev "$EXCLUDE"
  printf '%s\n' build.ps1 .gitmodules docs/BUILDING.md
} | while IFS= read -r f; do
  mkdir -p "$STAGE/$(dirname "$f")"
  cp "$f" "$STAGE/$f"
done
printf 'url=%s\ncommit=%s\n' "$URL" "$BASE" > "$STAGE/UPSTREAM"
sed "s/@COMMIT@/$COMMIT/" docs/RELEASE-README.md > "$STAGE/README.md"

# The extracted tree builds with scripts/build.sh, which reads UPSTREAM (there is
# no git checkout inside a zip).
python3 - "$DIST/stage" "$NAME" "$ZIP" <<'PY'
import os, sys, zipfile
base, name, out = sys.argv[1:4]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for d, _, fs in sorted(os.walk(os.path.join(base, name))):
        for f in sorted(fs):
            p = os.path.join(d, f)
            z.write(p, os.path.relpath(p, base).replace(os.sep, '/'))
PY

# Verify: list the zip and refuse anything that could be a ROM or an asset.
echo "Contents of $ZIP:"
python3 - "$ZIP" <<'PY'
import sys, zipfile
names = zipfile.ZipFile(sys.argv[1]).namelist()
bad = [n for n in names if n.lower().endswith(('.gba', '.sav', '.png', '.mid', '.wav', '.xlsx', '.ips'))
       or any(p in n.split('/') for p in ('reloaded', 'build', 'rom', 'roms'))]
files = [n for n in names if not n.endswith('/')]
print('  %d files; patches: %d; scripts: %d'
      % (len(files), sum('/patches/' in n for n in files), sum('/scripts/' in n for n in files)))
for n in files:
    if '/patches/' not in n:
        print('  ' + n)
if bad:
    print('FORBIDDEN files in the zip:', *bad, sep='\n  ')
    sys.exit(1)
print('OK: no ROMs, saves, images, audio, spreadsheets, IPS files or third-party folders.')
PY
echo "Wrote $ZIP"

#!/usr/bin/env bash
# Rebuilds the romhack's working copy from scratch inside WSL:
#   upstream alchemy at the pinned commit + the patch series in patches/.
# Usage (from WSL):  bash /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$HOME/alchemy}"
BASE="$(head -n1 "$ROOT/UPSTREAM_BASE" | tr -d '[:space:]')"

if [ -e "$DEST" ]; then
  echo "$DEST already exists; move it away first" >&2
  exit 1
fi

git clone --recurse-submodules https://github.com/PascalPixel/alchemy.git "$DEST"
cd "$DEST"
git checkout -b arena "$BASE"
git submodule update --init --recursive
git config user.name "${GIT_AUTHOR_NAME:-$(git config --global user.name || echo romhack)}"
git config user.email "${GIT_AUTHOR_EMAIL:-$(git config --global user.email || echo romhack@localhost)}"
git am "$ROOT"/patches/*.patch
make -j"$(nproc)" bootstrap
echo "Done. Build with: make -j\$(nproc) tbs-en"

#!/usr/bin/env bash
# Rebuilds the romhack's working copy from scratch inside WSL:
#   upstream alchemy at the commit this repo pins (the `alchemy` submodule)
#   + the patch series in patches/<game>/ applied on a branch.
# Usage (from WSL):
#   bash /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/setup.sh [GAME [DEST]]
# GAME is tbs (default) or tla; DEST defaults to ~/alchemy. Set SKIP_BOOTSTRAP=1
# to skip building the compilers (about 10 minutes), for checking patches only.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${1:-tbs}"
DEST="${2:-$HOME/alchemy}"
BRANCH="arena"
[ "$GAME" = "tbs" ] || BRANCH="arena-$GAME"
BASE="$(git -C "$ROOT" ls-files -s alchemy | awk '{print $2}')"
URL="$(git -C "$ROOT" config -f .gitmodules submodule.alchemy.url)"

if [ -z "$BASE" ]; then
  echo "The alchemy submodule is not recorded in $ROOT" >&2
  exit 1
fi
if [ -e "$DEST" ]; then
  echo "$DEST already exists; move it away first" >&2
  exit 1
fi

git clone "$URL" "$DEST"
cd "$DEST"
git checkout -b "$BRANCH" "$BASE"
git submodule update --init --recursive
git config user.name "${GIT_AUTHOR_NAME:-$(git config --global user.name || echo romhack)}"
git config user.email "${GIT_AUTHOR_EMAIL:-$(git config --global user.email || echo romhack@localhost)}"
if ls "$ROOT"/patches/"$GAME"/*.patch >/dev/null 2>&1; then
  git am --3way "$ROOT"/patches/"$GAME"/*.patch
fi
if [ -z "${SKIP_BOOTSTRAP:-}" ]; then
  make -j"$(nproc)" bootstrap
fi
echo "Done: $GAME patches on $BRANCH at $DEST. Build with: make -j\$(nproc) $GAME-en"

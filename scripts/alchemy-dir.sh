#!/usr/bin/env bash
# Where the upstream (alchemy) working copy lives. One lookup, shared by the
# scripts (alchemy_dir.py and alchemy-dir.ps1 do the same):
#   1. $ALCHEMY_DIR, if set
#   2. the first line of the git-ignored file .alchemy-dir in the repo root
#   3. <repo>/work/alchemy
# A leading ~ is expanded. A relative path is taken from the repo root.
# Run it to print the directory, or source it to get bsa_root and bsa_alchemy_dir.
_BSA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bsa_root() { printf '%s\n' "$_BSA_ROOT"; }
bsa_alchemy_dir() {
  local d="${ALCHEMY_DIR:-}"
  if [ -z "$d" ] && [ -f "$_BSA_ROOT/.alchemy-dir" ]; then
    d="$(head -n 1 "$_BSA_ROOT/.alchemy-dir" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  fi
  [ -n "$d" ] || d="$_BSA_ROOT/work/alchemy"
  case "$d" in
    "~") d="$HOME" ;;
    "~/"*) d="$HOME/${d#\~/}" ;;
  esac
  case "$d" in
    /*) ;;
    *) d="$_BSA_ROOT/$d" ;;
  esac
  printf '%s\n' "$d"
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then bsa_alchemy_dir; fi

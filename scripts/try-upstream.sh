#!/usr/bin/env bash
# Trial run of a newer upstream, in the WSL working copy (see alchemy-dir.sh). Called by
# scripts/try-upstream.ps1; it can be run by hand:
#   try-upstream.sh run OLD NEW [BRANCH]   rebase BRANCH (default arena) from the
#                                          pin OLD onto NEW on a scratch branch
#                                          (arena-trial), build it, and explain a
#                                          failure
#   try-upstream.sh restore [BRANCH]       go back to BRANCH
# The branch BRANCH itself is never changed. The report is also written to
# ~/try-upstream-report.txt.
# Exit: 0 builds, 2 dirty tree, 3 rebase conflict, 4 our patches break the build,
#       5 upstream itself does not build.
set -u
cd "$(bash "$(dirname "${BASH_SOURCE[0]}")/alchemy-dir.sh")" || exit 2
REPORT=~/try-upstream-report.txt

if [ "${1:-}" = restore ]; then
  git rebase --abort 2>/dev/null
  git checkout -q "${2:-arena}"
  exit 0
fi

OLD=$2
NEW=$3
BRANCH=${4:-arena}
: > "$REPORT"
say() { echo "$@" | tee -a "$REPORT"; }

if [ -n "$(git status --short)" ]; then
  say "Uncommitted changes in $PWD: commit or stash them first."
  exit 2
fi
NEWSHA=$(git rev-parse --short=10 "$NEW")
say "Trial: ${OLD:0:10} -> $NEWSHA  ($(git rev-list --count "$OLD..$NEW") upstream commits), carrying $BRANCH"

# What we touch of upstream (modified files; our new files cannot conflict).
say
say "Our edits to upstream files (added/removed lines):"
git diff --numstat --diff-filter=M "$OLD" "$BRANCH" | sort -rn | awk '{printf "  %5d +  %-4d %s\n", $1, $2, $3}' | tee -a "$REPORT"
say "Files we add: $(git diff --name-only --diff-filter=A "$OLD" "$BRANCH" | wc -l)"
git diff --name-only "$OLD" "$BRANCH" | sort > /tmp/ours.$$
git diff --name-only "$OLD" "$NEW" | sort > /tmp/theirs.$$
say
say "Files changed by both sides (where a conflict can happen):"
comm -12 /tmp/ours.$$ /tmp/theirs.$$ | sed 's/^/  /' | tee -a "$REPORT"
rm -f /tmp/ours.$$ /tmp/theirs.$$

# Rebase onto a scratch branch.
git checkout -q -B arena-trial "$BRANCH"
if ! git rebase --onto "$NEW" "$OLD" arena-trial > /tmp/rebase.$$ 2>&1; then
  say
  say "REBASE CONFLICT. Files, with the upstream commits that touched them:"
  for f in $(git diff --name-only --diff-filter=U); do
    say "  $f"
    git log --oneline "$OLD..$NEW" -- "$f" | head -5 | sed 's/^/      /' | tee -a "$REPORT"
  done
  say "Stopped at: $(git log -1 --format=%s REBASE_HEAD 2>/dev/null)"
  git rebase --abort
  git checkout -q "$BRANCH"
  rm -f /tmp/rebase.$$
  exit 3
fi
rm -f /tmp/rebase.$$
say
say "Rebase clean: $(git rev-list --count "$NEW..arena-trial") patches replayed."

# Build. Judge by the log and the ROM, not by an exit code echoed through wsl.
build() {
  local log=$1
  # The generated file lists name the sources of whichever tree was built last;
  # a source that is not in this tree stops make ("No rule to make target").
  rm -f out/tbs-en/tbs-en.gba out/tbs-en/deps.mk out/tbs-en/objects.mk
  make -j"$(nproc)" tbs-en > "$log" 2>&1
  [ -s out/tbs-en/tbs-en.gba ] && ! grep -q '\*\*\*' "$log"
}
LOG=~/try-upstream-build.log
if build "$LOG"; then
  say "Build OK: out/tbs-en/tbs-en.gba"
  say "(branch arena-trial is checked out; run the smoke scripts, then restore)"
  exit 0
fi

# Upstream itself builds with many warnings; only errors matter here.
ERRS=/tmp/errs.$$
grep -E '^[^ ]+:[0-9]+:|undefined reference|\*\*\*|cannot move location' "$LOG" \
  | grep -vi 'warning:' > "$ERRS"
say
say "BUILD FAILED with our patches. Errors:"
cut -c1-220 "$ERRS" | head -25 | tee -a "$REPORT"

# For each name the compiler or linker complains about, which upstream commits
# changed it? (git log -S finds commits that add or remove the text.)
say
say "Upstream commits that changed the names in those errors:"
grep -E '^[^ ]+:[0-9]+:|undefined reference' "$ERRS" \
  | grep -oE "[\`']([A-Za-z_][A-Za-z0-9_]*)'" | tr -d "\`'" | sort -u | head -15 \
  | while read -r id; do
      hits=$(git log --oneline "$OLD..$NEW" -S"$id" -- games | head -3)
      if [ -n "$hits" ]; then
        say "  $id"
        echo "$hits" | sed 's/^/      /' | tee -a "$REPORT"
      else
        say "  $id: no upstream commit changed it (ours, or defined elsewhere)"
      fi
    done
say
say "Upstream commits touching the files with errors:"
grep -E '^[^ ]+:[0-9]+:' "$ERRS" | cut -d: -f1 | sort -u | head -10 | while read -r f; do
  say "  $f"
  git log --oneline "$OLD..$NEW" -- "$f" | head -3 | sed 's/^/      /' | tee -a "$REPORT"
done
rm -f "$ERRS"

# Is it us, or upstream? Build the new upstream with no patches.
say
say "Building upstream $NEWSHA alone to tell whose fault it is..."
git checkout -q --detach "$NEW"
if build ~/try-upstream-pristine.log; then
  say "Upstream alone builds: the break is in our patches."
  git checkout -q "$BRANCH"
  exit 4
fi
say "Upstream alone does NOT build. Not our patches. See ~/try-upstream-pristine.log"
git checkout -q "$BRANCH"
exit 5

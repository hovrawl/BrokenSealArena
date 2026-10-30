# Workflow: how this repo works

## The model

```
BrokenSealArena (this repo)
├─ alchemy/            submodule: upstream PascalPixel/alchemy, pinned, untouched
├─ patches/tbs/*.patch the romhack for The Broken Seal
├─ patches/tla/        (later) the same ideas for The Lost Age
└─ scripts/, docs/, AGENTS.md, .claude/
```

The ROM is **built from source** (`~/alchemy`, in WSL): upstream at the pinned
commit with the patches applied on a branch. The repo stores only the patches and
the pin. A fresh machine runs `scripts/setup.sh` and gets the same tree.

## Why patches over source, not xdelta/BPS

xdelta, IPS and BPS are **binary** patches: they turn one ROM file into another.
They suit hacks made by editing a ROM directly. They do not fit this project:

- We change C source and text; the ROM is an output. A binary patch cannot say
  what changed, cannot be rebased onto a newer upstream, and breaks on every
  upstream commit that moves a byte.
- Porting to The Lost Age needs the *source* changes, not the bytes.
- Binary patches against a commercial ROM are still derived from it; source
  patches over a public decompilation, with no ROM in the repo, are cleaner.

So the source of truth is the patch series (`git format-patch`, applied with
`git am`). The same approach as pret-style decomp hacks, which usually keep the
changes as commits on a fork's branch; this repo keeps them as patches over a
pinned submodule so upstream stays pristine and nothing is destructive.

A BPS/xdelta file is still useful as a **release artifact** for players: build
`tbs-en.gba` from a clean checkout, then `flips --create` / `xdelta3 -e` against
the player's own original ROM (`tbs-en` reproduces the original byte for byte, so
that base is well defined). Do this when you ship, not as the working format.
Never publish the ROM itself.

## Daily work

See `AGENTS.md` (edit in `~/alchemy`, build, smoke-test, commit, export patches,
document). Each patch should stay one coherent change, guarded by a switch, with
a `docs/CHANGES.md` entry that includes port notes.

## Moving to newer upstream

Upstream moves only when we choose. Try it first, with nothing real touched:

```powershell
scripts\try-upstream.ps1                  # fetch, trial-rebase, build, smoke; back on arena after
scripts\try-upstream.ps1 -Target REF      # any ref ~/alchemy knows
```

It rebases a copy of `arena` onto the target on a scratch branch (`arena-trial`),
builds it, and runs `attendant`, `manager` and `win` (look at
`build\smoke\trial_*.png`). It reports which of our edits to upstream files
overlap upstream's changes, and on failure says which it is:

- **Rebase conflict** (exit 3): the files, with the upstream commits that touched
  them. Nothing is changed.
- **Our patches break the build** (exit 4): the compiler and linker errors, and for
  each name in them the upstream commits that changed it (`git log -S`), so a rename
  shows as a commit. Upstream alone builds.
- **Upstream itself does not build** (exit 5): not our fault; wait or pin earlier.

The report is also in `~/try-upstream-report.txt` (WSL), the build log in
`~/try-upstream-build.log`. A good trial is adopted with the commands below.
`scripts\check-submodule.ps1` runs first and fails if `alchemy/` is not exactly the
pinned commit.

```powershell
scripts\update-upstream.ps1            # new upstream commits, files both sides touch
scripts\update-upstream.ps1 -Apply     # rebase ~/alchemy's arena branch onto them
scripts\update-upstream.ps1 -Finish    # after resolving a conflict
```

`-Apply` rebases in WSL, then points the submodule at the new upstream commit and
re-exports the patches. Build, run the smoke scripts, review, commit the pin,
`patches/`, and `CHANGES.md`. Conflicts are most likely in
`battle/battle/formation.c`, `scene/battle_arena.c`, the overlay import lists
(`system/overlay/imports.inc`, `scene/import/battle_arena.s`), `text/en.po` and
`main.ld` (bank starts).

## Starting from scratch

```bash
git clone --recurse-submodules <this repo>
bash scripts/setup.sh tbs          # in WSL: upstream + patches, builds the compilers
cd ~/alchemy && make -j$(nproc) tbs-en
```

`rom/` is optional for The Broken Seal (it builds from source; the dump only
verifies the unmodified build), and required for the unfinished parts of The Lost
Age.

## The Lost Age plan

Upstream is still decompiling it (`recon/tla`, parts built from the owner's
dump). When it is complete enough to build:

1. Create branch `arena-tla` in `~/alchemy` from the pinned upstream.
2. Port the patches in `docs/CHANGES.md` order, using each entry's port notes;
   enemy/formation/ability tables, scenes, message ids, bank sizes and overlay
   imports differ. Export to `patches/tla/`.
3. Characters and data from The Lost Age then replace or extend what the TBS
   patches use (Djinn, Psynergy, party members, enemies). Decide whether the final
   hack is TLA-based only; the TBS series is then the reference port.

## Remotes

Create your own GitHub repo for this project and push it; the submodule's URL
stays upstream's. If you want upstream-friendly changes (bug fixes, documentation)
offered back, make those on a separate branch of your own fork of alchemy, never
mixed into this repo's patches.

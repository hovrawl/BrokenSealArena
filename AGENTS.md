# Broken Seal Arena: guide for agents

A Golden Sun: The Broken Seal romhack that turns the game into a team-versus-team
arena (CPU ladders, a party manager with stat, Djinn, Psynergy and item shops,
saving through the Pause menu). It is **a patch series over the upstream
decompilation [PascalPixel/alchemy](https://github.com/PascalPixel/alchemy)**,
not a fork. The long-term plan is to port the same patches to The Lost Age
(`games/tla`) once upstream has decompiled it, and to use its data and
characters in the one hack.

Read first: this file, then `docs/WORKFLOW.md` (how the repo works),
`docs/CHANGES.md` (what every patch does and why), `docs/ROADMAP.md` (what comes
next and the decisions waiting), `docs/UI.md` (the rules for any screen, window or
menu: read before building one), `docs/GOTCHAS.md` (traps
already hit), `docs/TESTING.md` (headless smoke tests) and `docs/memory/`.

## The one rule

**Never edit the `alchemy/` submodule's files.** It is pinned upstream, kept
pristine. All changes are commits on the `arena` branch of the WSL working copy
`~/alchemy` (a clone of upstream), exported to `patches/tbs/` as `git
format-patch` files. Nothing destructive happens to upstream or to a ROM.

## Layout

| Path | What |
|---|---|
| `alchemy/` | submodule: upstream at the pinned commit (the base the patches apply to) |
| `patches/tbs/` | the romhack: one patch per change, `git am` order |
| `patches/tla/` | (future) the Lost Age port |
| `scripts/` | `setup.sh`, `export-patches.ps1`, `update-upstream.ps1`, `smoke.ps1`, `smoke/` |
| `docs/` | `WORKFLOW`, `CHANGES`, `GOTCHAS`, `TESTING`, `memory/` |
| `build.ps1` | build in WSL and copy the ROM to `build\tbs-en.gba` |
| `rom/` | the owner's cartridge dump (git-ignored, never committed or published) |
| `build/` | build output and smoke screenshots (git-ignored) |
| `.claude/agents/` | subagent definitions for recurring jobs |

The working copy is `~/alchemy` inside WSL (Ubuntu). It builds on WSL's own disk
(the `/mnt/c` mount is far too slow and breaks file modes). Windows tools reach it
at `\\wsl.localhost\Ubuntu\home\nathan\alchemy`.

## Everyday loop

1. Edit in `~/alchemy` (branch `arena`). Guard each change behind a switch
   (`ARENA_BOOT`, `ARENA_LADDER`, `ARENA_TRAINING`, `ARENA_PAUSE_MENU`, all in
   `include/arena_config.h`).
2. Build: `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1`
   (output `build\tbs-en.gba`; if the emulator holds it open it writes
   `tbs-en.new.gba`). **Check the build log for `***` or the ROM's timestamp;
   do not trust an exit code echoed through `wsl`.**
3. Smoke-test headless and **look at the screenshots** before saying it works:
   `scripts\smoke.ps1 NAME.txt -Fresh`, then read `build\smoke\shots\sheet.png`.
4. Commit in `~/alchemy` (message ends with the Co-Authored-By line), run
   `scripts\export-patches.ps1`, update `docs/CHANGES.md`, commit this repo.

Upstream moves: `scripts\update-upstream.ps1` (look), then `-Apply`.

## Conventions

- One patch = one feature layer, in dependency order, each building on its own;
  squash false starts (history in `CHANGES.md` records what was tried and
  dropped). Our code goes in our own files (`arena_*.c`, `arena_config.h`,
  `module/arena.h`); upstream files get only short hooks, so a new upstream
  rebases cleanly. Run `scripts\try-upstream.ps1` before adopting one.
- Follow alchemy's rules for the code you touch: C89 with GNU extensions,
  `Module_PascalCase` functions, `gName` globals, `LOUD_CASE` constants,
  clang-format LLVM style. Byte-matching no longer matters for hack code, but
  keep upstream's lines unchanged where you can so rebases stay easy.
- Only `text/en.po` has the new messages; other editions do not build. English
  only.
- Do not publish, upload or commit ROMs, saves or anything extracted from them.
- Ask before anything outward-facing: pushing, creating remotes, publishing.

## What the user expects

- Visual quality that matches the game's own menus (the shops are the model),
  so reuse native windows, icons, message text and font; avoid canvas text.
- Verified work: build, smoke-test, look, then report. Say what was and was not
  checked.
- Non-destructive changes, documented well enough to port to The Lost Age.

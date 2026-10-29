# Romhack changes against upstream alchemy

This project is a patch series on top of
[PascalPixel/alchemy](https://github.com/PascalPixel/alchemy), pinned at the
commit in `UPSTREAM_BASE`. Nothing from upstream is copied here: the whole
romhack is the `.patch` files in `patches/`, one per commit, plus the notes
below. That keeps the diff against upstream small and lets us rebase onto a
newer upstream, or onto The Lost Age (`games/tla`), later.

Target: **The Broken Seal, English (`tbs-en`)**. Edition-specific work (other
languages) is not done; the changes below are guarded so they can be turned off.

## Workflow

| Task | How |
|---|---|
| Set up from scratch (WSL) | `bash /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/setup.sh` |
| Build | `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1` (ROM to `build\tbs-en.gba`) |
| Edit | work in `~/alchemy` (WSL), branch `arena`, and commit there |
| Save the work | `scripts\export-patches.ps1`, then commit this repo |
| Move to newer upstream | in `~/alchemy`: `git fetch origin && git rebase origin/main arena`, fix conflicts, update `UPSTREAM_BASE`, export |

Upstream's `make compare-*` checks no longer pass. They compare against the
original ROM bytes, and the romhack changes them on purpose.

## Changes

Each entry names the patch, the files, the switch that disables it, and what
to look at when porting.

### 1. New Game boots into the Battle Arena
- Patch: `0001-Arena-New-Game-boots-straight-into-the-Battle-Arena.patch`
- Files: `games/tbs/src/scene/file_screen.c`,
  `games/tbs/src/scene/import/file_screen.s`
- Switch: `ARENA_BOOT` (top of `file_screen.c`; `0` restores the prologue).
- What: in the file screen's New Game branch, after
  `MainRoutineWork_InitializeDefaults`, add Garet, Mia and Ivan to the party,
  level all four to 30, set `FLAG_IN_BATTLE_ARENA`, and send the game to
  `SceneId_BattleArena` (the same destination the stock Battle option uses).
  No save file is read or written.
- Overlay imports: overlays only reach functions listed in
  `scene/import/<scene>.s`; this adds `Unit_LevelUpTo` and `Unit_Calculate`.
- Port notes: the file screen and the arena scene are separate overlays; a
  `tla` port needs the equivalent scene names.

### 2. Team ladder replaces level-matched monster battles
- Patch: `0002-Arena-team-ladder-replaces-level-matched-monster-bat.patch`
- Files: `games/tbs/include/battle/formations.h`,
  `games/tbs/src/battle/formations.c`,
  `games/tbs/src/battle/battle/formation.c`
- Switch: `ARENA_LADDER` (top of the ladder code in `formation.c`).
- What: `gArenaLadder[12]` lists fixed mixed teams (rows of
  `game/enemy_table.c`) with a target level each. Under `FLAG_MONSTER_BATTLE`,
  `BattleFormation_BuildEnemyList` takes the team for the series' current win
  count (`gMainRoutineWork.linkTallies[3]`, the arena's monster streak) instead
  of calling `BattleFormation_SelectLevelMatchedCandidate`. Enemies are scaled
  by the existing `BattleEnemy_AdjustLevel` through `levelAdjustment`.
- Limits: a small enemy uses one of six sprite slots and any other two
  (`BattleSprite_IsSmall`); keep every rung within six. Rungs 1 to 3 are
  play-tested; the rest are not.
- Port notes: formation and enemy rows differ in The Lost Age; re-pick the
  teams from its `enemy_table.c`.

### 3. Training menu (stats and Psynergy)
- Patch: `0003-Arena-training-menu-for-stats-and-Psynergy.patch`
- Files: `games/tbs/src/scene/battle_arena.c`,
  `games/tbs/src/scene/import/battle_arena.s`,
  `games/tbs/src/system/overlay/imports.inc`,
  `games/tbs/src/scene/file_screen.c` (starting coins)
- Switch: `ARENA_TRAINING` (top of `battle_arena.c`).
- What: `Training_Run` opens a full-screen window (the debug menus' pattern:
  `Window_Create`, `Text_Draw*`, keys from `gKeysRepeat`) with a character
  list, a stat screen and a Psynergy shop. Stats add to the unit's `base*`
  fields and call `Unit_Calculate`; Psynergy goes through
  `Unit_LearnPsynergy`. Prices: HP = base, PP = 2 x base, Attack 3 x,
  Defense and Agility 4 x, Luck (base + 1) x 100; Psynergy 150 + 50 per PP.
  `gTraining_PsynergyShop` is the shop list (ability ids; names come from
  `MsgAbilityName`).
- Hooks: after a monster win (`BattleArena_RunRoundResult`, which also pays
  the coins: 200 plus 100 per earlier win in the series) and at the start of
  the attendant's talk (`BattleArena_ChooseBattleMode`). It heals the party
  (`Party_RestoreHpPp(1)`) on exit.
- Overlay imports: `Unit_LearnPsynergy` had no row in `imports.inc`, so one
  was added (its far stub already existed in `gamepak/far_call/GAME.S`).
- Not done: the upgrades live in RAM only. They persist only if the stock save
  is used; this build has no save step yet. Text is English only, written as
  global `const u8` arrays (scene overlays use no string literals elsewhere).
- Port notes: ability ids and enemy/unit layouts match across the two games
  only partly; check `ability_table.c` in The Lost Age.

## Planned

- Save and load the upgraded party.
- Stock arena text still mentions link cables.
- Stock arena resets the party to Isaac, Garet, Ivan and Mia on a save load.

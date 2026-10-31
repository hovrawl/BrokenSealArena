# Romhack changes against upstream alchemy

This project is a patch series on top of
[PascalPixel/alchemy](https://github.com/PascalPixel/alchemy), pinned as the
`alchemy` submodule. Nothing from upstream is copied here: the whole romhack is
the `.patch` files in `patches/tbs/`, one per feature layer, plus the notes
below. That keeps the diff against upstream small and lets us rebase onto a
newer upstream, or onto The Lost Age (`games/tla`), later. `docs/WORKFLOW.md`
explains the model.

Target: **The Broken Seal, English (`tbs-en`)**. Edition-specific work (other
languages) is not done; each change below has a switch that turns it off.

## Workflow

| Task | How |
|---|---|
| Set up from scratch (WSL) | `bash /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/setup.sh` |
| Build | `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1` (ROM to `build\tbs-en.gba`) |
| Edit | work in `~/alchemy` (WSL), branch `arena`, and commit there |
| Save the work | `scripts\export-patches.ps1`, then commit this repo |
| Try a newer upstream | `scripts\try-upstream.ps1` (trial rebase, build, smoke), then `scripts\update-upstream.ps1 -Apply`; see `docs/WORKFLOW.md` |

Upstream's `make compare-*` checks no longer pass. They compare against the
original ROM bytes, and the romhack changes them on purpose.

## How the hack is arranged

**Our code lives in our own files; upstream's files get hooks.** The patches add
these files and edit upstream's only where they must (about 115 lines of hooks
and table rows, plus the `en.po` messages):

| File | What |
|---|---|
| `include/arena_config.h` | the switches `ARENA_BOOT`, `ARENA_LADDER`, `ARENA_TRAINING`, `ARENA_PAUSE_MENU` (define one as 0 to take that part out) |
| `include/module/arena.h` | what our files export to each other |
| `src/scene/arena_boot.c` | New Game into the arena (file screen overlay, object `370`) |
| `src/battle/battle/arena_ladder.c` | the team ladder (a part of `battle.c`) |
| `src/window/screens/arena_icon_menu.c` | the shop-style icon menu (a part of `screens.c`) |
| `src/shop/shop/arena_shop.c` | the member picker and the stat, Djinn and Psynergy counters (a part of `shop.c`) |
| `src/scene/arena_menu.c` | the attendant's and the manager's menus (arena overlay, object `3cb`) |
| `src/window/screens/arena_save.c` | saving in the arena (a part of `screens.c`) |
| `src/scene/arena_series.c` | the series flow: give up, round reports, clearing (a part of `battle_arena.c`, which it needs for its statics) |

Some upstream objects are unity builds ("Part of shop.c"): new code for them goes
in a new part file included from the parent, not in a new object. Hooks that stay
in upstream files: `file_screen.c`, `formation.c`, `battle_arena.c`, `save.c`,
`settings_menu.c`, `run.c`, one include each in `battle.c`, `shop.c`, `screens.c`,
the far-call rows (`WINDOW.S`, `SHOP.S`), the import rows (`imports.inc`, the
overlays' `import/*.s`), `objects.tsv` rows and a bank start in `main.ld`.

## The patches

Each is one layer, in order; each builds on its own.

### 1. The switches and the header our files share
- Patch: `0001-Arena-the-switches-and-the-header-our-files-share.patch`
- Files: `include/arena_config.h`, `include/module/arena.h` (new).
- No behaviour. Every hook includes `arena_config.h`, so the switches are in one
  place. `arena.h` is where our files declare what they share, so upstream's
  headers stay as they are.

### 2. The messages for the arena's menus
- Patch: `0002-Arena-the-messages-for-the-arena-s-menus.patch`
- Files: `text/en.po` (the `MsgArena*` messages, appended).
- Why messages: text drawn from C strings uses a different, monospaced font and
  does not wrap. Messages draw in the game's own font. Numbers and names go
  through messages too: `MsgArenaNumber` (`{argument_signed_number}`) and
  `MsgArenaName` (`{argument_actor_name:1}`), with `MessageArgument_Push` before
  the draw. The win report is the attendant saying `MsgArenaVictory`. Icon-menu
  labels are *consecutive* messages (`IconMenu_Center` takes a base).
- **Editions:** only `en.po` has them. The other five `.po` files are untouched,
  so those editions do not build (the code names messages they lack).
- Message keys must be contiguous from 0 (`validateCatalog` in
  `tools/ags-text/catalog.c`); new messages go at the end and `MsgEnd` moves up
  with them. `X-Alchemy-Symbol-Count` is the glyph alphabet, not a message count.
- There is no cursor or up-arrow glyph in any message, so the names say "Up".

### 3. New Game boots into the Battle Arena
- Patch: `0003-Arena-New-Game-boots-straight-into-the-Battle-Arena.patch`
- Files: `scene/file_screen.c` (a hook), `scene/arena_boot.c`,
  `scene/import/file_screen.s` (imports `Unit_LevelUpTo`, `Unit_Calculate`),
  `objects.tsv`.
- Switch: `ARENA_BOOT`.
- What: in the New Game branch, after `MainRoutineWork_InitializeDefaults`,
  `ArenaBoot_NewGame` adds Garet, Mia and Ivan, levels all four to 30, gives
  1500 coins, sets `FLAG_IN_BATTLE_ARENA` and sends the game to
  `SceneId_BattleArena` (the stock Battle option's destination). No save file is
  read or written, and there is no Battle option in this flow.
- It also sets `restartScene` and `restartEntrance` to the arena, so Continue on a
  file saved by another build of the ROM (every rebuild is one) lands in the
  arena instead of at a Sanctum.
- Overlay imports: overlays reach only functions listed in
  `scene/import/<scene>.s`.
- Port notes: the file screen and the arena are separate overlays; a `tla` port
  needs the equivalent scene names.

### 4. Team ladder replaces level-matched monster battles
- Patch: `0004-Arena-a-team-ladder-replaces-level-matched-monster-b.patch`
- Files: `battle/battle/arena_ladder.c`, `battle/battle/formation.c` (hooks),
  `battle/battle.c` (one include).
- Switch: `ARENA_LADDER`.
- What: `gArenaLadder[12]` lists fixed mixed teams (rows of
  `game/enemy_table.c`) with a target level each. Under `FLAG_MONSTER_BATTLE`,
  `BattleFormation_BuildEnemyList` takes the team for the series' win count
  (`gMainRoutineWork.linkTallies[3]`, the arena's monster streak) instead of
  calling `BattleFormation_SelectLevelMatchedCandidate`. Past the last rung it
  fights the last again, a level stronger for each win. Enemies are levelled by
  the existing `BattleEnemy_AdjustLevel` through `levelAdjustment`.
- Limits: a small enemy uses one of six sprite slots and any other two
  (`BattleSprite_IsSmall`); keep every rung within six. Rungs 1 to 3 are
  play-tested; the rest are not, and round 3 spikes with a boss.
- Port notes: formation and enemy rows differ in The Lost Age; re-pick the teams
  from its `enemy_table.c`.

### 5. The shop-style icon menu and the party manager's screens
- Patch: `0005-Arena-the-shop-style-icon-menu-and-the-party-manager.patch`
- Files: `window/screens/arena_icon_menu.c`, `shop/shop/arena_shop.c`,
  `gamepak/far_call/WINDOW.S` and `SHOP.S` (one or two exports each),
  `shop/shop.c` and `window/screens.c` (one include each), `main.ld`.
- Why in the main image: these use private state (the shop's work block, the
  icon menu) and have no far-call stubs, so an overlay cannot drive them. They
  sit beside that state and are exported.
- `ArenaMenu_IconChoose(prompt, icons, labelBase, count)`: the prompt opens as a
  message window the way `Shop_ShowKeeperMessage` does
  (`Message_OpenWindow(prompt, 5, 0, 0x22)`), then `IconMenu_Open`/`AddIcon`/
  `Center` (tile row 17) and the stock `IconMenu_Run`. The label is `labelBase`
  plus the position. **Keep icon rows to four**: five or more left the prompt's
  window without its text (VRAM cache pressure). `COMMAND_ICON_EQUIP` does not
  draw in the arena; `COMMAND_ICON_ATTACK` does.
- `ItemPicker_ChooseMember(mode)`: the shops' strip of walking figures, then what
  to show beside it. Modes: 0 items (as the shops' Sell), 1 Djinn, 2 Psynergy,
  3 status. Djinn and Psynergy and status share a 30 by 10 tile panel across the
  top (224 by 64 pixels inside, first pixel at screen 8, 8; 11 tiles tall); no
  coins window in those modes.
  - Djinn: an animated figure and the name, three columns of 16-pixel rows (12
    shown). The figure is an actor `Sprite` (ids 90 to 93, one per element,
    animation 2 for a set Djinni), not per Djinni; it needs
    `Render_ApplyProjectedPlacement` every frame, at scale `0xb000`, placed by
    its feet (x the cell's icon centre, y the bottom of the cell). A sprite that
    cannot be created leaves the element's icon tile (`0x5001` plus element).
  - Psynergy: a 16-pixel ability icon
    (`WindowSprite_CreateFromResource(ICON_KIND_ABILITY, ...)`, sentinel 252 as
    the shops do) and the name, two columns of four rows (8 shown).
  - Status: a copy of the Status screen's top rows, not a call, because
    `ItemMenu_DrawMemberStatus` reads the field menu's work and the shop's work
    holds the same bytes as something else. Conditions are not shown, only
    "Normal".
  - Tile text snaps to an 8-pixel row: a 16-pixel row puts the name at y + 8 and
    the icon at y + 4, as the Status screen does.
- `ArenaShop_Run(kind, unitId)`: counters built like `Shop_SelectBuy`: the stock
  row (seven a page, page arrows, a price tag from `Shop_CreatePriceSprite`), the
  hand cursor (`MenuCursor_Place`), the name/price window (as
  `Shop_DrawItemPrice`), the coins window (`Shop_DrawMoney`) and the description
  (`Shop_DrawMessage`), with `MsgWhatWouldYouLike`. Left/Right move one with wrap,
  Up/Down a page, A buys, B leaves. Kinds: 0 Psynergy, 1 Djinn, 2 stats.
  - Psynergy: ability icons, the chosen one swelling as in the shops; the
    description is `MsgAbilityDescription` plus the ability id; price 150 plus 50
    for each PP of cost.
  - Djinn: the element's animated figure; the description is the Djinni's
    ability (`ABILITY_DJINNI_FIRST` plus its number); 500 coins each.
  - Stats: HP (+20), PP (+10), Attack, Defense and Agility (+5), Luck (+1). Each
    entry uses the icon of the item that raises that stat for good, `<stat> Up`
    for its name and "Raises X by n. Now m." for its description (the two numbers
    pushed with `MessageArgument_PushFar` just before the draw). Prices scale with
    the character's base stat (`ArenaStat_Cost`). At a stat's cap the price window
    says MAX and a purchase does nothing. Stats add to the unit's `base*` fields
    and call `Unit_Calculate`; Psynergy goes through `Unit_LearnPsynergy`.
- **Bank size:** the shop code is in bank `rom_main_06`, which had 114 bytes to
  spare and overflowed by about 2 KB (`cannot move location counter backwards` at
  `main.ld`). Bank 07's start moved from `0x080b5000` to `0x080b6000` for
  `tbs-en` (it had 5 KB free). Check the slack in `out/tbs-en/tbs-en.map` before
  adding code to a bank.
- `gMenuWork` is shared: the shop's `ShopWork` and the field menu's work occupy
  the same block, so shop code must not call menu-bank functions that read the
  other layout.
- Not done: custom icon art (the game's command icons are fixed graphics with
  fixed names, so some do not suit their label).
- Port notes: ability and Djinn ids, the sprite ids for the figures and the
  bank layout all need checking in The Lost Age.

### 6. The attendant's and the party manager's menus
- Patch: `0006-Arena-the-attendant-s-and-the-party-manager-s-menus.patch`
- Files: `scene/arena_menu.c` (new object `3cb`), `scene/battle_arena.c` (hooks),
  `scene/import/battle_arena.s`, `system/overlay/imports.inc`, `objects.tsv`.
- Switch: `ARENA_TRAINING`.
- Attendant (`BattleArena_ChooseBattleMode` hook): `ArenaMenu_AttendantMode` asks
  Solo or Multiplayer, then for Solo the tournament. Solo takes the stock "start a
  monster series" branch, Multiplayer the stock "wait for a link" branch; the
  stock yes/no question is skipped (`answer` is set from the menu). It is not
  asked when a series is already running. The Monster Gauntlet (`gArenaLadder`)
  is the only tournament; a second needs a way for the battle code
  (`ArenaLadder_Select`) to know which one was chosen, for example a game flag
  byte.
- Party manager (`BattleArena_PartyManager`): replaces the talk trigger of
  `ACTOR_LINKED_WINS_TELLER`, the man to the right of the counter (the linked-win
  reporting is no longer reachable). Characters (the status panel and the stat
  counter), Djinn, Psynergy, and Items, which opens the real `Shop_Run` on Xian's
  weapon, armor and item stock rows (16 to 18). The party is healed on the way
  out, since stats and gear may have changed.
- Wins: after a monster win (`BattleArena_RunRoundResult`) the attendant says
  `MsgArenaVictory` with the coins won, 200 plus 100 for each earlier win in the
  series, and the party is healed (`Party_RestoreHpPp(1)`).
- Overlay imports: functions the new code calls need a row in `imports.inc`
  (their far stubs mostly existed: `Unit_LearnPsynergy`, `Window_ClearInteriorTiles`,
  `Sprite_Create`, ...) and in `import/battle_arena.s`. Scene overlays have no
  string literals or static data of their own: use global `const` arrays.
- The list screens call `Window_ClearInteriorTiles` before every redraw; without
  it the previous draw showed through wherever new text was shorter. Canvas text
  (`Text_DrawString`, `Text_DrawNumber`) ignores it and uses a different font;
  use the tile calls.
- Actor ids such as `ACTOR_ATTENDANT` are defined inside `battle_arena.c`, so
  `arena_menu.c` takes them as parameters.
- Port notes: scene, actor and trigger names differ in The Lost Age.

### 7. Saving through the Pause menu
- Patch: `0007-Arena-saving-through-the-Pause-menu.patch`
- Switch: `ARENA_PAUSE_MENU`.
- Files: `field/field_sequence/run.c`, `window/window/settings_menu.c` (hooks),
  `window/screens/arena_save.c`, `window/screens/save.c` (hooks),
  `window/screens.c` (one include).
- The Start (Pause) menu already has Save your quest, Sleep and Change settings.
  Two things shut it in the arena: the field answers `MsgFieldPauseUnavailable`
  when `FLAG_IN_BATTLE_ARENA` is set (`run.c`), and `PauseMenu_Open`/`Choose` show
  only Change settings under that flag (`settings_menu.c`). Both are bypassed.
- Save is the game's own `Save_ToChosenFile` (file list, overwrite question). A
  save holds the whole game state, so base stats, Psynergy, Djinn, items and
  coins persist.
- `ArenaSave_Begin`/`ArenaSave_End` set `next`/`entrance` to the arena at
  `BATTLE_ARENA_FROM_FILE_SCREEN` for the write, then put both back. Without it a
  load enters with the last battle's entrance (`BATTLE_ARENA_AFTER_MONSTER_WIN`)
  and pays its reward again. (This patch also cleared `FLAG_MONSTER_BATTLE` for
  the write, so a load started a new series; patch 9 stopped that.)
- Loading: the title's Continue.
- History: an earlier attempt put Save in the party manager's menu. A fifth icon
  made the prompt's window open without its text, and a second attempt gave it a
  person to talk to; both were dropped for the Pause menu.

### 8. A series you can leave, give up, clear or lose
- Patch: `0008-Arena-a-series-you-can-leave-give-up-clear-or-lose.patch`
- Switch: `ARENA_TRAINING`.
- Files: `scene/arena_series.c` (new, a part of `battle_arena.c`),
  `scene/battle_arena.c` (hooks and the spawn row), `include/module/arena.h`
  (`ARENA_LADDER_COUNT`, now 12, shared with the ladder), `text/en.po` (three
  messages).
- A Gauntlet is twelve rounds. After a win (`BattleArena_RunRoundResult`) the
  attendant says "Round n of 12 won! Step into the circle when you are ready."
  and the series **keeps running**: the stock Yes/No (whose No ended the series) is
  gone. The player stands outside the circle, facing it, and steps in when ready,
  so the manager and its heal sit in between. The `BATTLE_ARENA_AFTER_MONSTER_WIN`
  spawn moved from inside the circle (z 200) to z 240, facing north: inside, the
  stock flow starts the next fight at once ("Good luck!").
- Talking to the attendant while `FLAG_MONSTER_BATTLE` is set asks "Round n of 12.
  Do you want to give up?" (`ArenaSeries_GiveUp`). Yes ends the series
  (`ArenaSeries_End`: the flag and win count cleared, "You won n battles.", the best
  streak kept); No says the stock "Good luck!". Not a loss: the losses tally is
  untouched. With no series running the attendant shows the Solo/Multiplayer menu.
- Clearing round 12 (`linkTallies[LINK_TALLY_MONSTER_STREAK]` reaches 12) is a win
  and ends the series with "You cleared the Monster Gauntlet! Congratulations!".
- A loss ends the series as before (stock loss line, losses tally, the standard
  spawn) and now restores the party to full HP and PP.
- The stock "record" write is skipped under this switch
  (`BattleArena_SaveMonsterBattleResults` returns at once). It writes 16 bytes of
  the file with its own saving messages into a "current file", which does not exist
  after a New Game. The tallies live in `gMainRoutineWork.linkTallies` and are saved
  with the game. Per-tournament stats are possible (the saved struct has unnamed
  spare bytes) and are on the roadmap.
- Traps found (also in `GOTCHAS.md`): ending a series before any fight must clear
  `FLAG_BATTLE_ARENA_PLAYER_AGREED` (which starting one sets) or the link poll
  reports "The link was disconnected."; a field message with two number blanks
  shows the first number twice, so "of 12" is in the message text and the code
  asserts the constant.
- Port notes: the attendant, trigger and flag names differ in The Lost Age; the
  spawn row and the circle position need checking there.

### 9. A series in progress is saved and resumed
- Patch: `0009-Arena-a-series-in-progress-is-saved-and-resumed.patch`
- Files: `window/screens/arena_save.c` only (a smaller `ArenaSaveState`).
- A series needs two things to survive a save, and both were already saved:
  `FLAG_MONSTER_BATTLE` is 0x173, a persistent game flag (the scene and area temp
  ranges start at 0x200 and are cleared on scene or area changes), and the win
  count (`linkTallies[3]`, the round) is in the saved `MainRoutineWork`. Patch 7
  cleared the flag for the write; this patch stops, so Continue resumes the
  Gauntlet at the same round and the attendant asks "Round n of 12. Do you want to
  give up?". The entrance is still overridden to the arena's door, so the last
  battle's reward is not replayed.
- It fixes a bug in patch 7: saving mid-series showed "The link was disconnected."
  (the flag was cleared for the write while `FLAG_BATTLE_ARENA_PLAYER_AGREED`, a
  scene temp flag that is saved raw, stayed set, which the link poll reads as a
  lost link).
- The tournament was not stored here (there was only one); patch 10 stores it.
- Smoke: `resume.txt` saves mid-series, restarts the console (the new `reset`
  driver command), chooses Continue, reads the tally and flag with `peek`, and
  talks to the attendant.

### 10. A second tournament: the Boss Rush, a tournament flag, no healing
- Patch: `0010-Arena-a-second-tournament-the-Boss-Rush-with-a-tourn.patch`
- Files: `include/module/arena.h` (the flag and the tournament macros),
  `battle/battle/arena_ladder.c` (a second ladder, a tournament-aware
  `ArenaLadder_Select`), `scene/arena_series.c`, `scene/arena_menu.c`,
  `text/en.po` (five messages).
- **The tournament flag.** `FLAG_ARENA_TOURNAMENT` is 0x7f8, a persistent byte flag
  (byte 0xff of `gGameFlagBytes`, read with `GameFlag_GetByteFar` in the main image
  and `FieldGameFlag_GetByte` in an overlay), so a save and Continue keep it. How it
  was chosen: persistent flags are those below 0x200 and 0x400 upward (0x200 to
  0x2ff are scene temps, 0x300 to 0x3ff area temps, cleared on a change). Every
  computed range was excluded: the Djinn (from 0x100), the Psynergy tints (0x148),
  the visited areas (0x180), the shop stock (0x400 plus a row, 35 rows),
  `ENEMY_DEFEATED_FLAG(classId)` (0x600 plus an enemy, `battle_internal.h`), and the
  clusters of story flags (0x800 to 0x9f0, 0xec0 to 0xfd7) with their offsets. The
  band 0x7f8 to 0x7ff has no name and no computed use anywhere in `games/tbs/src`
  or `include`. More bytes can be claimed downward from it; list them in `arena.h`.
- **The tournament menu** has two icons and labels (`MsgArenaTournamentGauntlet`
  and `MsgArenaTournamentBossRush`, consecutive). The Boss Rush uses the Summon icon
  (a dark silhouette, which suits a boss). The choice is written to the flag when
  Solo is chosen.
- **Per-tournament data.** `ARENA_ROUNDS(t)` gives 12 or 6 rounds; the ladder is
  `gArenaLadder` (12) or `gArenaBossRush` (6). The Boss Rush's rungs are bosses:
  Orc Lord and Lizard King, Manticore and Chimera, Tempest Lizard and Cerebus,
  Saturos and Menardi, Deadbeard and the Hydros Statue, then the Fusion Dragon
  alone, at target levels 14, 22, 30, 36, 41 and 45 (data only; not balanced).
  Rows are enemy ids less `ENEMY_ID_FIRST` (8).
- **Messages per tournament.** Each tournament has three consecutive messages (give
  up, next round, cleared), so `MsgArenaGiveUpPrompt + 3 * t + kind` finds them. The
  round count is in the text ("of 12", "of 6"), asserted against the macros in
  `arena_series.c`.
- **Healing is a tournament setting.** `ARENA_HEALS(t)` is false for the Boss Rush.
  `ArenaMenu_ShowWin` skips the heal after a win, and the manager's exit skips it
  while a series is running (outside a series it heals as before, so the manager
  cannot undo it mid-run). After a loss the party is restored as before. Without
  healing, the way to recover is items and the field menu's Cure.
- Smoke: `tournaments.txt`, `rungs_rush.txt`, `rush_round.txt` (HP carried into the
  next fight), `heal_round.txt` (the Gauntlet's contrast), `rush_manager.txt` (the
  manager's exit does not heal), `rush_clear.txt` and `resume_rush.txt`.
- Not done: the Boss Rush is not balanced (round 1 cannot be won by pressing A);
  per-tournament stats; the scripts that need a won round use a test trick (start as
  the Gauntlet's easy first team, then set the byte to the Boss Rush).
- Port notes: the flag byte, the tournament macros and the message layout port as
  they are; re-pick the bosses from the Lost Age's enemy table.

### 11. Isaac and Garet start with the Short Sword
- Patch: `0011-Arena-Isaac-and-Garet-start-with-the-Short-Sword-so-.patch`
- Files: `scene/arena_boot.c`, `scene/import/file_screen.s` (imports `Inventory_Equip`).
- A new game gives Isaac and Garet a Machete (`character_table.c`). While it is
  equipped the battle draws it as part of their own **prologue** sprites
  (`SPRITE_ISAAC_MACHETE`, `SPRITE_GARET_MACHETE`, no weapon overlay;
  `battle/placement.c`). The game swaps it for an equipped Short Sword when the
  prologue ends (`Party_EndChildhood`), which gives the normal sprites with the
  weapon drawn over them. The arena's New Game skips the prologue, so they stayed on
  the first sprites. `ArenaBoot_NewGame` now does that one swap for the two of them
  before it calculates their stats (Attack rises by 2: Isaac 146, Garet 129).
- Deliberately not done: the rest of `Party_EndChildhood` (300 coins, Move and
  Retreat for Isaac, Move for Garet, Mind Read for Ivan, a few story flags), so the
  Psynergy shop's stock and the coin economy are unchanged. `FLAG_CHILDHOOD` was
  already clear in the arena (checked with `peek`), so classes were never the cause.
- Port notes: the Lost Age has its own starting equipment and sprite special cases;
  look for the same kind of "drawn as part of the sprite" check.

### 12. Quitting before winning a round
- Patch: `0012-Arena-quitting-before-winning-a-round-says-Try-again.patch`
- Files: `scene/arena_series.c`, `text/en.po` (`MsgArenaTryAgain`).
- Giving up with no wins ends the series with "Try again next time!" instead of
  the stock "You won 0 battle." (its `{plural_suffix}` treats zero as singular):
  they did not want to compete, so the line is generic. With wins it is unchanged.

### 13. Linked battles are four a side
- Patch: `0013-Arena-linked-battles-are-four-a-side-ARENA_LINK4.patch`
- Switch: `ARENA_LINK4` (`arena_config.h`, on by default).
- Files: `scene/battle_arena.c` (the lobby sends and receives four unit records),
  `game/units.c` (the opponent's Djinn recovery table moves from enemy unit 3 to 4),
  `battle/battle/arena_link.c` (new: opponent layout and the half-size sprite map),
  hooks in `placement.c`, `battle.c`, `battle_internal.h`, `main.ld`, `sprites.tsv`,
  `layout.tsv`.
- A spike, proved with `scripts/smoke/link.c` (two consoles, lockstep): a 4v4 runs to
  a result, with Attack, Psynergy and a Djinn crossing the link. See `MULTIPLAYER.md`.
- Eight 64x64 characters fill sprite VRAM, so the opponents use 32x32 sheets made at
  build time (`scripts/gen-opponent-sprites.py`, run by `build.ps1`) with no weapon.
  The ROM grows 20 KB (`main.ld` start of the last region, `ROM_END_tbs` on the make line).
- Port notes: the Lost Age has eight characters; its party order and sprite ids differ.
  Not yet tested: Djinn recovery over several turns, Summons, hacked against stock.

## Dropped on the way

- The first training menu was a full-screen canvas-text window with its own list
  screens, then paged icon grids. They were replaced by the shop-style counters
  in layer 5 once it was clear the shops are the model. The original thirteen
  chronological patches are in this repo's history: `patches/tbs/` at commit
  `01a3234`, the one before the re-slice (the branch that held them in `~/alchemy`
  has been deleted).

## Planned

- Save the Gauntlet rung; more tournaments.
- A balance pass (round 3 spikes with a boss; rungs 4 to 12 are untested).
- Stock arena text still mentions link cables.
- Stock arena resets the party to Isaac, Garet, Ivan and Mia on a save load.
- Characters beyond the four (needs CHILD sprites), other editions, and the Lost
  Age port.

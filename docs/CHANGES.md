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
  Tested since: Djinn recovery over several turns and a Summon (see `MULTIPLAYER.md`).

### 14. Say so when the linked opponent is another version
- Patch: `0014-Arena-say-so-when-the-linked-opponent-is-another-ver.patch`
- Switch: `ARENA_LINK4`. Files: `scene/battle_arena.c`, `text/en.po`
  (`MsgArenaLinkOtherGame`).
- The four-a-side build publishes its own lobby signature word (`BSA4`). While the
  player waits for an opponent, a partner with another word for a second (a stock game,
  or a build with another party size) makes the attendant say "Your opponent has a
  different version of the game!" and stop waiting, through the disconnect event. The
  stock side stays silent, since the stock lobby only leaves such a console out.
- Port notes: only the English signature is changed; other editions do not build.

### 15. The Reloaded engine rules: level-up, ailments, damage
- Patch: `0015-Arena-the-Reloaded-engine-rules-level-up-ailments-an.patch`
- Switches: `ARENA_RULES_LEVELUP`, `ARENA_RULES_AILMENTS`, `ARENA_RULES_DAMAGE`
  (`arena_config.h`), **on by default** (patch 16); they run over the stock tables until the
  rebalance's data is ported.
- Files: `game/game/arena_rules.c` (new part of game.c: the level gain and the effect
  rate tables), hooks in `levels.c`, `battle_arithmetic.c` and `battle/battle/ability.c`.
- See `RELOADED.md` (the decision) and `RELOADED-ENGINE.md` (each rule, how it was
  checked, and the code changes still to decode). Level-up is checked against the
  rebalance's own level 99 stats; bosses (luck 40 and up) are immune to most ailments
  in its table, which we can edit.
- Port notes: the Lost Age has its own patch (v1.83) and eight characters; the same rules
  apply, with different addresses.

### 16. New games start at level 50, the Reloaded rules on
- Patch: `0016-Arena-new-games-start-at-level-50-and-the-Reloaded-e.patch`
- `ARENA_START_LEVEL` 50 (`module/arena.h`, was a literal 30 in `scene/arena_boot.c`), and
  the three `ARENA_RULES_*` switches default to on.
- Psynergy is learnt by class and level (the last at 54 in the stock table), so level 50
  opens every pool and the Djinn alone decide the class.
- Checked: a New Game's base stats at level 50 equal the closed form of the level-up rule
  with the game's own growth curves, for all four characters (HP, PP, attack, defense,
  agility, luck); a Gauntlet battle runs to victory.
- Existing saves keep their stats; only a New Game levels up.

### 17. More Reloaded engine rules: guard, heal, revive, effect ids, stages, recovery
- Patch: `0017-Arena-more-Reloaded-engine-rules-guard-heal-revive-e.patch`
- Switches (`arena_config.h`, all on): `ARENA_RULES_GUARD`, `_HEAL`, `_REVIVE`,
  `_EFFECT_IDS`, `_DURATIONS`, `_STAGES`, `_RECOVERY`, `_STATUS`, `_CLASS20`, `_CAPS`,
  `_ITEMS`, `_SUMMON_TURNS`; `ARENA_RULES_AILMENTS` also sums the Ailment attribute.
- Files: short hooks in `battle/battle/ability.c`, `action.c`, `setup.c`, `turn_end.c`,
  `game/game/units.c`, `battle_arithmetic.c`, `menu/menu/use.c`,
  `window/screens/battle_status.c`; `BattleWork.arenaTurn` (the byte no stock code named).
- Each rule, its address in the original and how it was checked: `RELOADED-ENGINE.md`.
  What is deliberately not ported (UI layout, graphics resources) is listed there too.
- **Needs the data port**: `_EFFECT_IDS` (ability and enemy effect ids) and `_CLASS20`
  (class multipliers doubled) change the meaning of data; on stock data Confuse acts as
  Delude and class stats halve. `_REVIVE` keeps stock amounts for an ability of power 0.
- **Design changes the rules make**: summons wait for turn 2 or 3 (`_SUMMON_TURNS`), a
  deluded unit cannot unleash, Total Defense takes a third, Defense stages are stronger.
- Checked: built with every switch 0 and every switch 1, a Gauntlet battle fought both
  ways, the turn counter read in a battle (`scripts/smoke/rules_turn.txt`), and several
  rebuilt functions compared with the patched original.

### 18 to 26. The Reloaded data port
The data of the Golden Sun Reloaded rebalance (v1.83a; credit: its authors, forum topic
2779, in each table's header) written into our tables, so the engine rules of patches 15
to 17 have the data they were made for. One converter, `scripts/port-reloaded-tables.py`,
read the IPS and an unmodified build and rewrote the fields that differ (rows, comments and
layout kept, named constants where our headers have them); **the source no longer depends
on the patch**. Switches stay as they were (`ARENA_RULES_*`); with the data in, the
stock-data caveats of patch 17 (Isaac's HP halved, Confuse as Delude) are gone.

| Patch | Layer | What changed |
|---|---|---|
| 18 `Reloaded-ability-data` | `ability_table.c`, `arena_config.h` | 292 of 519 rows: power, PP cost, ranges, effects; abilities 23 and 81 to 83 are new (Jupiter damage); `ARENA_EFFECT_*` names for the effect ids (36 to 41, 43, 54) that the stock enum names badly |
| 19 `Reloaded-class-data` | `class_table.c`, `character.h`, `ability.c` | 96 of 203 rows: the six multipliers in twentieths (CLASS20), Psynergy and learning levels, vulnerabilities; **`ClassDefinition.weakEffects[3]` is now the field `ward`** (struct size unchanged) |
| 20 `Reloaded-item-data` | `item_table.c` | 133 of 324 rows: weapons, armour, accessories, prices, unleashes, healing items, effect 24 (Ailment) |
| 21 `Reloaded-enemy-data` | `enemy_table.c`, `element_table.c` | 159 of 165 enemy rows (stats, Psynergy sets, weaknesses by the aliased ids, drops) and 41 of 44 element presets |
| 22 `Reloaded-growth-curves` | `character_table.c`, `djinn_table.c` | the 5 characters with curves (level 99 stats equal the workbook's) and 28 of 80 Djinn |
| 23 `Reloaded-battle-animations` | `ability_staging.c` | 33 of 519 entries of `gAbilityBattleEffects`: the new abilities and the variants |
| 24 `Reloaded-text` | `text/en.po`, table comments | 227 messages decoded from the patch's message archive (names, descriptions with the new numbers); the tables' `// Name` comments follow |
| 25 `Psynergy shop prices` | `arena_shop.c` | the shop kept a copy of each spell's PP cost; it now asks the ability table |
| 26 `lobby signature` | `battle_arena.c` | the signature word is `BSR4` when the Reloaded rules are on (`BSA4` before): consoles with different rules do not link |

- **How it was checked**: `scripts/table-check.py` compares every table of our built ROM
  with the stock ROM with the IPS applied in memory: **0 of 519 abilities, 203 classes, 324
  items, 165 enemies (bytes 30 to 39 aside, see below), 44 presets, 8 characters, 80 Djinn
  and 519 battle effects differ**. The message archive of our ROM equals the patched stock's
  in all 10,723 stock messages. Spot checks against the workbooks (`workbook-check.py`):
  96 spells (PP and power) all but the nine explained ones, 39 weapons and 53 armours
  (price and bonus) all but four that are The Lost Age's, 93 class rows (88 equal; five differ by one twentieth in one stat, the sheet's rounding or an edit after it); level 99 stats for
  Isaac, Garet, Ivan and Mia equal the "Lv99 Character Stats" sheet. Built, and the
  smokes `stats`, `battle`, `win`, `psynergy`, `manager`, `items`, `djinn`, `rungs`, `rules_turn`
  looked at.
- **Not ported (listed so nobody looks for it)**: enemy bytes 30 to 39 of 11 rows (bosses
  and Mimics: the patch writes small numbers there, which no code of the patched game
  reads that we found); graphics (the Psynergy icons it redraws, menu panels); `gFormations`
  (8 bytes), `gBattleSprites` (one entry), shop stock (`sStockTable`), inn prices,
  `gItem_ArtifactSlotTable`. The changelog's "non-overworld Djinn can't escape" is probably
  in `gFormations` (not confirmed) and is not ported.
- **Arena code that reads these tables**: `arena_shop.c` (fixed, patch 25); `arena_ladder.c`
  keys on enemy rows, which the patch does not reorder, so every rung still shows the same
  monsters, but their stats are the story game's retune: at level 50 the party is far ahead
  of the early rungs (a Skeleton hits for about 10), a balance pass for later.

### 28. No win streak after a cup, no Game Tickets
- Patch: `0028-Arena-no-win-streak-after-a-cup-and-the-shops-give-n.patch`
- The attendant no longer tells the streak when a series ends (the best is kept for the endless
  challenge); the shops give no Game Ticket after a purchase (`Shop_BuySpecialItem`).

### 29. Equipment-only cup rewards, and the Djinn reset after a fight
- Patch: `0029-Arena-cup-rewards-are-equipment-only-more-of-it-and-.patch`
- Cup rewards are gear only; more of it (the Unicorn Ring, and drops of the cup's enemies, listed
  by `scripts/cup-drops.py`). After each fight every Djinni is set again and the party's
  recovery list is emptied (`ArenaMenu_RestoreDjinn`). Checked with `scripts/smoke/djinn_reset.txt`
  (a Djinni poked onto standby is set again after the win) and `cup_reward_item.txt` (Fur Coat).

### 30. Cup gear spread over each cup's whole stretch of the story
- Patch: `0030-Arena-cup-gear-is-spread-over-the-whole-story-stretc.patch`
- A cup pays the equipment of everything between the previous cup's boss dungeon and its own
  (chests, gifts, and the rare drops of the stretch's mobs), in story order, at most two a
  round, each piece dearer than the earlier one of its type. The stretch table is
  `scripts/cupstretch.py` (scenes in story order and encounter regions per cup); `cup-gear.py
  --equip` and `cup-drops.py` list by it. Added: Vambrace (Altin), Turtle Boots (Lunpa), Lure
  Cap, Lucky Cap, Thunder Crown, Dragon Scales and Gaia Blade (Lighthouse); the Lighthouse
  gear now runs over rounds 1 to 9. 47 of the 64 reward flags are used. Checked with
  `cup_reward_item.txt` (Fur Coat, round 5) and `cup_reward_item2.txt` (Lighthouse round 6:
  Feathered Robe and Asura's Armor, once). Left out: Colosso prizes (weak) and Bandit's Sword.
  The story position of Vault, Vault Cave, Hammet Palace and Xian is a guess (marked in
  `cupstretch.py`).

## Dropped on the way

- The first training menu was a full-screen canvas-text window with its own list
  screens, then paged icon grids. They were replaced by the shop-style counters
  in layer 5 once it was clear the shops are the model. The original thirteen
  chronological patches are in this repo's history: `patches/tbs/` at commit
  `01a3234`, the one before the re-slice (the branch that held them in `~/alchemy`
  has been deleted).

## 27. The cup framework (patch 0027)

Implements docs/CUP-SPEC.md (owner's revision). **A cup is data** and never sets the
party or its level.

- **Source of truth: `scripts/cupdata.py`.** `scripts/gen-cups.py` (run in WSL) writes
  `include/module/arena_cups.h`, `src/battle/arena_cups.c` (teams; its own object, row in
  `objects.tsv`, `rom_tail_00`, because bank 07 had no room), `src/scene/arena_cup_info.inc`
  (info, rewards, shop rows; included by `arena_menu.c`), `src/shop/shop/arena_djinn_gate.inc`
  and the message block at the end of `text/en.po` (between the GENERATED CUPS comments:
  keep it last). `scripts/cup-check.py` verifies enemy ids, sprite slots (six), the Djinn
  (each obtained once) and items; `scripts/cup-gear.py` lists chests by cup.
- **Cups:** 0 to 6 the main cups A Tret, B Mercury, C Mogall, D Altin, E Tolbi, F Lunpa,
  G Lighthouse; 7 Boss Rush (side, opens after G); 8 Crossbone Isle (side, Deadbeard).
  The Monster Gauntlet is gone. Old saves' tournament byte 0 or 1 now names other cups.
- **State:** `FLAG_ARENA_PROGRESS` 0x7f0, `FLAG_ARENA_SIDE_CLEARED` 0x7e8, reward bits
  0x7a0 to 0x7df (35 used). Persistent; the Pause-menu save keeps them.
- **Attendant:** Solo then Next cup / Replay / Side cups (icon rows of at most four; Early
  and Later groups when more than four are replayable), "Enter the X Cup?", Yes starts.
  Only open cups are offered. The counter-style list of the spec was not built.
- **First clear of a main cup:** the attendant's scene (what opens), the party raised to
  the cup's level (`Unit_LevelUpTo`, never down), progress advances. Replays only
  congratulate. Rewards (Djinni won in a round, chest gear) are given once, after the round.
- **Manager:** Djinn counter lists only Djinn on sale (4 at the start, more per cup);
  item shops follow the last cup cleared; the Psynergy shop is removed. New Game is level 10.
- `main.ld` unchanged. Item shop rows other than Xian's were not visited in the arena.

## 31. Onboarding: the greeter's introduction (patch 0031)

- **Behaviour:** the first time on a save that the player talks to the greeter
  (`ACTOR_GREETER`, sprite 0x6c at (192, 272), beside the New Game spawn), she shows
  `MsgArenaGreeterIntro1` and `2`, three pages each: cups one region at a time; talk to the
  girl in the circle, choose Solo, enter the first cup; a win makes the party stronger and
  puts new Djinn on sale at the party manager; shops and the next cup open, older cups can be
  replayed; gear is found as cup rewards, side cups follow the main line; Multiplayer in the
  circle for two players. After that she says her stock welcome.
- **State:** `FLAG_ARENA_ONBOARDED` = 0x7e0, the byte at index 0xfc (verified free in
  `flags.h`, GOTCHAS and CUP-SPEC 5.1). Set when the second message ends; `ArenaBoot_NewGame`
  clears it. A Pause-menu save keeps it (`resume.txt` peeks it).
- **Code:** `BattleArena_TalkToGreeter` in `battle_arena.c`, switch `ARENA_ONBOARDING`
  (`arena_config.h`, default on). The two messages sit above the generated cup block in
  `en.po`, which therefore moved by two ids; `gen-cups.py` was re-run.
- **Not done:** no automatic start when the player walks near her; the scene's step triggers
  are tile areas by id and the talk is enough. In a smoke run the A press that starts New Game
  also talks to her, which is why `to_lobby.txt` now taps three more times.

## 32. Trophies in the lobby (patch 0032)

- **Behaviour:** one trophy actor per cup (nine), in a row along the ledge above the entrance
  pits (z 268; x 120 to 174 and 240 to 308, the entrance lane between), each placed when its
  flag is set. Bronze (cups 1, 2), silver (3, 4), gold (5, 6), crowned gold (7), blue (the two
  side cups). The lane in front of the counters stays walkable (`trophies_reach.txt`).
- **State:** `FLAG_ARENA_TROPHY_FIRST` = 0x790, bit n = cup n has been cleared (0x790 to 0x798;
  0x790 to 0x79f claimed), set in `ArenaSeries_Cleared` at the first clear. Not derived for
  older saves (new saves only).
- **Art:** `scripts/gen-trophy-sprites.py` (run by `build.ps1`; outputs git-excluded)
  makes `spr_309` to `313`, 16 x 32, one picture, the field sprites' palette; rows in
  `sprites.tsv`, `layout.tsv`. 32 x 32 sprites were tried first and exhausted the sprite VRAM
  cache: the first line of message windows drew as noise. With 9 trophies plus both NPCs at
  16 x 32 text is clean, but the margin is unknown; the lobby shows 28 placed rows of 58.
- **Rows:** `ACTOR_TROPHY_FIRST` to `ACTOR_TROPHY_LAST`, added to both placement tables before
  the party rows (party rows have sprite ids below 8 and take no placed id). Not shared sprites
  (`ACTOR_PLACEMENT_SHARE_PREVIOUS_SPRITE` dereferences the previous actor unchecked).

## 33. Champion and scout (patch 0033)

- Placed actors `ACTOR_CHAMPION` (sprite 0x71, after cup 7) and `ACTOR_SCOUT` (0x87, after cup
  3) beside the door, conditioned on the trophy flags. Talk is a `MSGNO` trigger row, no
  handler: `MsgArenaChampion` and `MsgArenaScout` (2 pages each) above the generated cups
  block; `gen-cups.py` re-run (ids moved by two). Test: `npcs.txt`, `npc_scout.txt`.

## 34. The file list shows cups (patch 0034)

- `SaveFileSummary.djinn[4]` is now `cups[4]`: cups cleared per tier (bronze 0-1, silver 2-3,
  gold 4-6, side cups), counted by `Save_BuildFileSummary` from the trophy flags. The file
  list draws four trophy sprites (309, 310, 311, 313) over two-digit counts; none for a tier
  at 0, no window when all are 0. Functions renamed `FileList_*TrophySprites/Counts`. Same code
  for Continue and the Pause-menu Save. No paging (the four tiers need none; L and R are free
  in the list if wanted). Tests: `filelist_cups.txt`, `filelist_cups_all.txt`.

## 36. Display cases in the lower wings (patch 0036)

- **Behaviour:** nine always-present display cases (sprite 314, 16 x 32, art by
  `gen-trophy-sprites.py`: wooden frame, glass, low plinth) stand in a row along the south edge
  of the two lower wings: four on the left (x 70, 88, 106, 124) and five on the right (x 303,
  318, 333, 348, 363), z 280. Left = main cups 1 to 4, right = main cups 5 to 7 and the two side
  cups. The nine trophy actors moved into them (the old row above the pits is gone); an empty
  case is a goal, a won cup shows inside the glass.
- **Rows:** the cases are the last nine rows of both placement tables (`ACTOR_CASE_FIRST` on,
  after the party rows) so no enum number changed. The first case loads the sprite and the other
  eight use `ACTOR_PLACEMENT_SHARE_PREVIOUS_SPRITE`; with 9 separate loads the champion's
  first message line drew as noise again, with sharing it is clean. No talk.
- **Depth:** actors sort by z in coarse steps (about 8 pixels: z 285 against 284 tied and the case
  hid the trophy), and `height` lifts the picture without changing the sort. So the trophy is at
  z 288 with height 7 (drawn 4 pixels above the case's foot, in front), the case at z 280. Do not
  put a case at z 270: the map's barrels (z <= 262, x 71 to 88 and 340 to 368) push it away.
- **Moved NPCs:** only the wary visitor (sprite 0x74, was (72, 288) in the corner) moved, to (84, 124), the upper left landing, in both tables, same row (patch 0037; (172, 228) beside the attendant blocked the link script's route to her and the 4v4 never started). The man at (104, 248) and the girl at (328, 248) stand
  above the cases and stay. The right wing's last case must not be right of x 363.
- Sprite memory: one extra 16 x 32 picture; text windows clean in `onboarding.txt`, `npcs.txt`.
- Tests: `cases_0/3/9.txt` (walk into both wings; `build\smoke\shots\cases_N.png` joins the left
  and right views, `scripts/compose-shots.py`). Port notes: depth and sharing rules above.

## 38. A trophy appears at once after the first clear (patch 0038)

- `ArenaSeries_Cleared` sets the trophy flag and then calls `Event_SpawnActorPlacements` on the
  scene's table (`gFieldWork->tables[1]`, from `ACTOR_FIRST_PLACED`): it creates the actors whose
  condition now holds and puts the existing ones back in their places (they stand still). No
  reload. The attendant's menu, the manager's Djinn and shop stock and the Djinn gate read the
  progress byte live and were right already (`trophy_refresh_menu.txt`: the menu offers the
  Mercury Cup straight after the clear). Test `trophy_refresh.txt` (first clear, then walk into
  the lower left wing: the trophy stands in the first case).

## 39. A trophy design for every cup (patch 0039)

- Nine 16 x 16 placeholder sprites, cup order: 309 cup, 310 pennant, 311 shield, 312 star on a
  plinth, 313 sword in a stone, 315 laurel wreath, 316 crown, 317 gem on a plinth, 318 mask
  (bronze, silver, gold, blue by tier). `gen-trophy-sprites.py` holds the art as ASCII pictures
  (one letter a colour role); rows 315 to 318 of `sprites.tsv` / `layout.tsv`; both placement
  tables use them (case and flag order unchanged). Redraw by editing the pictures or replacing
  the PNGs.
- **Sprite memory** (`vram_peek.txt` + `scripts/vram-count.py`): lobby with all nine trophies, the
  champion and the scout standing, 350 of 512 blocks used, 162 free; with no cups 282 used. So
  nine distinct trophies cost 36 blocks and both NPCs 32; every message window drew clean
  (`trophies_text_all.txt`: the greeter's six introduction pages with all nine; `npcs.txt`).
- The extra sprite data overflowed the ROM region before the last one ("cannot move location
  counter backwards"): `main.ld` starts the last region at 0x08326000 (was 0x08325000) and
  `build.ps1` pads to `ROM_END_tbs=0x08806000`. Watch this when adding more sprites.

## 40. The file list pages the trophies (patch 0040)

- `SaveFileSummary.cups[4]` is now `cupBits[4]`: bit n set when cup n is cleared (32 cups fit;
  size unchanged). The list draws the cups' own trophies, five to a page; a cup not won is the
  same sprite in grey (`Sprite_SetAnimationColorModesFar(.., SPRITE_COLOR_GREY)`). Under them the
  page indicator "1/2" (`Text_DrawNumberAtOffset` and a "/"); it is drawn for every file with a
  cup (the page total is `ARENA_CUP_COUNT` over five), so there is no stale text. L and R turn
  the page (wrapping, with the cursor sound); up and down reset it to page 1. The fifth sprite
  slot is the first Djinn-menu `phases` word of the menu work (a gap the shop's party sprites do
  not reach). The Continue list and the Pause-menu Save list are the same code (checked in
  `filelist_pages.txt`). New saves only. `sFileListTrophySprites` must grow with the cup count.

## 41. The scout and the champion move (patch 0041)

- Scout (0x87) at (160, 268) facing east, champion (0x71) at (272, 268) facing west: the south
  strip of the hall, at the pits' edge, 56 px from the spawn lane, clear of the door and the old
  man, the counters' fronts (z 236 to 250), the circle, the cases (x 124 and 303, z 280) and the
  wing floors. Both placement tables. Tests: `npcs.txt`, `npc_scout.txt`, `npc_all.txt`,
  `npcs_moved.txt` (the old routes up to the door were replaced).

## 42. A warning before a boss round (patch 0042)

- `cupdata.py`: `R(..., boss=0/1/2)`; when left out `finish_bosses()` derives it: the last round
  of a main cup (or of a side cup that holds a story boss) and every Boss Rush round are bosses
  (2); a round with a story boss (`STORY_BOSSES`) that is not last is a mini-boss (1). Written
  as two bitmasks in `ArenaCupInfo` (`miniBossRounds`, `bossRounds`; bit n is the round after n
  wins). After "Round n won!" the attendant shows `MsgArenaBossWarning` ("Watch out! The next
  round is a boss!") or `MsgArenaMiniBossWarning` ("Careful! A tough opponent is next!") as one
  more window when round n + 1 is marked. Round 1 has none. Marked: Tret, Mercury, Mogall, Altin,
  Tolbi, Lunpa, Lighthouse last rounds, minis: Altin 8, Tolbi 7, Lunpa 9, Lighthouse 9; Boss
  Rush all; Crossbone 10. Tests `boss_warning.txt` (Tret, round 8) and `boss_warning_mini.txt`.

## 43. Stat boosts won by rounds replace the coin stat shop (patch 0043)

- **Which items.** Power Bread (HP +8), Cookie (PP +4), Apple (Attack +5), Hard Nut (Defense +3),
  Mint (Agility +4), Lucky Pepper (Luck +1): `menu/menu/use.c` says which raises what (the old
  shop's icons were wrong; fixed) and `ability_table.c` the amount. They are no longer given as
  items. `cupdata.py` `BOOSTS` attaches the ones the story put in each cup's stretch (chests,
  jars, gifts; `cup-gear.py` lists them) to rounds as `("boost", stat)` rewards, 22 in all: Tret
  HP r2, Attack r3; Mercury Defense r2, r4; Mogall Luck r1, Attack r4; Altin PP r1, HP r2, Luck r4,
  Agility r5, r7, r8; Tolbi Attack r1, HP r3, PP r5; Lunpa Attack r1, HP r3, Defense r4, PP r8;
  Crossbone Luck r2, PP r5, Defense r8. Left out: one Hard Nut in `cottage_rooms_b` (no cup's
  stretch names the scene). The two Mints in `log_rooms_a` and `_b` share a cell behaviour, so
  they may be one box in the story; both are counted.
- **Pool.** One pool per stat for the whole party. The EARNED count is a persistent byte flag per
  stat, `FLAG_ARENA_BOOSTS + 8 * stat` (0x740 to 0x76f, `module/arena.h`); the once-only reward
  bits are in their own block 0x770 to 0x78f (`ARENA_BOOST_REWARD_FLAG_FIRST`), since the main
  block of 64 was nearly full. Winning the round the first time bumps the byte and the attendant
  says "You can boost HP once more!" (`MsgArenaBoostGet*`, generated). New games start at zero.
- **Spending.** The party manager's Stats counter (same place, same screens) is free: the tag
  under each icon and the right window ("Boosts left") show what is left of the stat, the price
  window shows "Used" (applied across the party). A is "apply to this character" (+ the item's
  amount to the base stat), "No boosts left" when the pool is empty, MAX at the stat cap
  (`ArenaStat_Cap`, unchanged). A new last entry, Reset, gives every applied boost back and
  restores the stats ("All boosts are back.").
- **Applied is derived, not stored.** `Unit_GetLevelBase` (`levels.c`; far call
  `Unit_GetLevelBaseFar`) sums `ArenaRules_LevelGain` over levels 1 to the unit's level: the base
  stats from levelling alone. Applied = (base now - that) / amount; used = the sum over the
  party. Cup level raises (`Unit_LevelUpTo`) add the same gains, so it stays valid; equipment and
  Djinn are not in the base. Reset writes the closed form back to the base and recalculates.
  Checked at level 10 (new game) and level 15 (after a Tret clear). If a later patch adds
  base-stat changes of another kind (class change, a Lost Age port with other growth), it breaks.
- Tests: `boost_reward.txt` (message and pool), `boost_shop.txt` (screens, Isaac, Garet, empty
  pool, Reset), `boost_resume.txt` (save, restart, Continue: pool kept), `boost_level.txt` (level
  15). The screens are in `build\smoke\keepoost_*.png`.

## Planned

- Save the Gauntlet rung; more tournaments.
- A balance pass (round 3 spikes with a boss; rungs 4 to 12 are untested).
- Stock arena text still mentions link cables.
- Stock arena resets the party to Isaac, Garet, Ivan and Mia on a save load.
- Characters beyond the four (needs CHILD sprites), other editions, and the Lost
  Age port.

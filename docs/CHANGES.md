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

### 4. Attendant and party manager menus
- Patch: `0004-Arena-attendant-and-party-manager-menus.patch`
- Files: `games/tbs/src/scene/battle_arena.c`,
  `games/tbs/src/scene/import/battle_arena.s`,
  `games/tbs/src/system/overlay/imports.inc` (a row for
  `Window_ClearInteriorTiles`; its far stub already existed)
- Switch: `ARENA_TRAINING` (also guards patch 3).
- `ArenaMenu_Choose(prompt, options, count)`: a prompt window across the top
  and up to six options across the bottom (three to a column, A chooses, B
  cancels). There is no shop-style icon row: the game's command icons are
  fixed graphics with fixed names, so this one draws plain text.
- Attendant (`BattleArena_ChooseBattleMode`): `ArenaMenu_AttendantMode` asks
  Solo or Multiplayer, then for Solo the tournament. Solo takes the stock
  "start a monster series" branch, Multiplayer the stock "wait for a link"
  branch; the stock yes/no question is skipped (`answer` is set from the menu).
  Not asked when a series is already running. Tournaments: the Monster
  Gauntlet (`gArenaLadder`) is the only one. A second would need a way for
  battle code (`ArenaLadder_Select`) to know which one is chosen, for example
  a game flag byte.
- Party manager (`BattleArena_PartyManager`): replaces the talk trigger of
  `ACTOR_LINKED_WINS_TELLER`, the man to the right of the counter (the
  linked-win reporting is no longer reachable). Characters (stats), Djinn
  (all 28, 500 coins, given and set at once through `Djinn_Give` and
  `Djinn_Set`), Psynergy (patch 3's shop), and Items, which opens the real
  `Shop_Run` on Xian's weapon, armor and item stock rows (16 to 18).
- After a win, `ArenaMenu_ShowWin` shows the coins won and heals the party; the
  training menu no longer opens by itself.
- The screens call `Window_ClearInteriorTiles` before every redraw. Without it
  the previous draw showed through wherever the new text was shorter.
- Build note: `make` through `wsl ... ; echo rc=$?` reported 0 on a failed
  build; check the log for `***`, or that the ROM's timestamp changed.

### 5. Shop-style icon menus and the character strip
- Patch: `0005-Arena-shop-style-icon-menus-and-character-strip.patch`
- Files: `games/tbs/src/window/screens/icon_menu.c` (new
  `ArenaMenu_IconChoose`), `games/tbs/src/shop/shop/item_picker.c` (new
  `ItemPicker_ChooseMember`), `gamepak/far_call/WINDOW.S` and `SHOP.S` (one
  export each, appended to the bank tables), `system/overlay/imports.inc`,
  `scene/import/battle_arena.s`, `include/module/window/screens.h`,
  `include/module/shop/shop.h`, `scene/battle_arena.c`.
- Why in the main image: the icon menu and the shop's party strip use private
  state and have no far-call stubs, so an overlay cannot drive them. The new
  functions live beside that state and are exported.
- `ArenaMenu_IconChoose(prompt, icons, labels, count)`: a prompt window across
  the top, and `IconMenu_Open`/`AddIcon`/`Center` for the icon row at tile row
  17, as `Menu_SelectShopCommand` does. Each icon's name is a fixed message
  (`MsgCommandName + icon`), so the label is drawn from the caller's text. Icons
  used: Fight and Cable (Solo, Multiplayer), Battle (the gauntlet), Status,
  Djinn, Psynergy and Item (the manager), Equip, Defend and Item (the shops).
  They are existing art, so some do not suit their label.
- `ItemPicker_ChooseMember()`: `ItemPicker_Run` without the item choice, plus
  the coins window from `Shop_ChooseMember`. Returns the unit id or -1.
- The list screens now use the tile text calls (`Text_Draw*InWindow`,
  `Text_DrawMessageAsTiles`) at 16-pixel rows. The canvas calls
  (`Text_DrawString`, `Text_DrawNumber`) ignore `Window_ClearInteriorTiles`,
  which left old cursors and numbers showing.
- Not done: custom icon art. That, or labels, would need new resources (the
  game's text is `text/*.po`, six files, one set of numbered messages).

### 6. Menu text as game messages
- Patch: `0006-Arena-menu-text-as-game-messages-icon-highlight-foll.patch`
- Files: `games/tbs/text/en.po` (30 messages appended, `MsgArena*`, ids
  10723 to 10752), `scene/battle_arena.c`, `window/screens/icon_menu.c`,
  `include/module/window/screens.h`.
- Why: text drawn from C strings uses a different, monospaced font and does not
  wrap. Messages draw in the game's own font. The first patch-5 menu also kept
  its own selection counter, so the icon highlight did not follow the label.
- `ArenaMenu_IconChoose(prompt, icons, labelBase, count)` now opens the prompt
  as a message window the way `Shop_ShowKeeperMessage` does
  (`Message_OpenWindow(prompt, 5, 0, 0x22)`), then runs the stock
  `IconMenu_Run`, with `labelBase` as `IconMenu_Center`'s label messages (label =
  `labelBase` + position; hence consecutive messages).
- Numbers and names go through messages too: `MsgArenaNumber`
  (`{argument_signed_number}`) and `MsgArenaName` (`{argument_actor_name:1}`),
  with `MessageArgument_Push` before the draw. They draw left-aligned.
- The win report is the attendant speaking `MsgArenaVictory`.
- **Editions:** only `en.po` has the new messages. The other five `.po` files
  are untouched, so those editions do not build with these changes (the code
  names messages they lack). Message keys must be contiguous from 0
  (`validateCatalog` in `tools/ags-text/catalog.c`); `X-Alchemy-Symbol-Count`
  is the glyph alphabet, not a message count, and is left alone. New messages go
  at the end; `MsgEnd` moves up with them.
- The list screens' cursor is still a tile `>` (no cursor glyph exists in any
  message), and the party strip has no custom text.

### 7. Djinn and Psynergy panels, paged purchase grids
- Patch: `0007-Arena-Djinn-and-Psynergy-panels-and-paged-icon-purcha.patch`
- Files: `shop/shop/item_picker.c`, `include/module/shop/shop.h`,
  `scene/battle_arena.c`, `scene/import/battle_arena.s`,
  `system/overlay/imports.inc`, `text/en.po` (`MsgArenaNone`, `MsgArenaPage`).
- `ItemPicker_ChooseMember(mode)`: 0 shows the member's items as before, 1 their
  Djinn, 2 their Psynergy, in a 30 by 10 tile panel across the top (the coins
  window moves to row 10 for those two). Djinn: element icon tile plus name, three
  columns of eight-pixel rows (24 at most). Psynergy: 16-pixel icon plus name,
  two columns of four rows (8 at most). The rest are not shown.
- A Djinni's "sprite" is its element's icon tile (window tile `0x5001` plus the
  element), which is what the game's Djinn lists use. Creature sprites are
  battle and field actors and are not available in a window.
- Psynergy icons: `WindowSprite_CreateFromResource(ICON_KIND_ABILITY, id, ...)`,
  as the Psynergy menu does; its far stub existed, so the import row was added.
  The icon's `sentinel` is set to 252 as the shops do for item icons.
- `Training_RunGrid` (battle_arena.c) replaces the two list screens: icon and
  name cells, two columns by six rows (12 a page), a `>` marker, price or
  Known/Owned under the grid and "Page n/m". Left/Right move by one, Up/Down
  by a row, L/R by a page. `WindowSprite_PrepareForRedraw` clears the window
  and its sprites each redraw.
- The Characters menu still uses the item strip and the stat list.

### 8. Animated Djinni figures
- Patch: `0008-Arena-animated-Djinni-figures-in-the-Djinn-picker-and.patch`
- Files: `shop/shop/item_picker.c`, `scene/battle_arena.c`,
  `scene/import/battle_arena.s`, `system/overlay/imports.inc`.
- The creature in the Djinn menu is an actor `Sprite` (ids 90 to 93, one per
  element, `gDjinnFigures_SpriteIds`), animation 2 for a set Djinni. It is not
  per Djinni: a Mercury Djinni of any name is the same figure.
- Each visible Djinni gets `Sprite_Create(VENUS_DJINNI + element)`,
  `Sprite_StartAnimation(.., 2)`, and a `Render_ApplyProjectedPlacement` call
  every frame (the sprite is not drawn otherwise), as
  `DjinnFigures_UpdateAllPositions` does, at scale `0xb000` (about 0.69). A
  sprite that cannot be created leaves the icon tile in its place.
- Positions assume the window's first pixel is at screen (8, 8) and that the
  figure stands at its feet: x = cell icon centre, y = bottom of the cell.
- The picker panel's Djinn rows are now 16 pixels (12 shown), to fit a figure.
  The purchase grid makes its 12 figures when the page changes.
- Imports added (stubs existed in `FIELD.S`): `Sprite_Create`,
  `Sprite_Destroy`, `Render_ApplyProjectedPlacement`.

### 9. Psynergy and Djinn counters like the Buy counter
- Patch: `0009-Arena-Psynergy-and-Djinn-counters-built-like-the-shops.patch`
- Files: `shop/shop/item_picker.c` (`ArenaShop_Run` and helpers),
  `gamepak/far_call/SHOP.S`, `system/overlay/imports.inc`,
  `include/module/shop/shop.h`, `scene/battle_arena.c`,
  `scene/import/battle_arena.s`, `games/tbs/main.ld`.
- `ArenaShop_Run(kind, unitId)` follows `Shop_SelectBuy`: the stock row
  (`stockItemIds`, seven a page, page arrows, a price tag from
  `Shop_CreatePriceSprite` under each entry), the hand cursor
  (`MenuCursor_Place`), the name/price window (as `Shop_DrawItemPrice`), the
  coins window (`Shop_DrawMoney`) and the description in the bottom window
  (`Shop_DrawMessage`). The prompt is `MsgWhatWouldYouLike`. Left/Right move by
  one with wrap, Up/Down by a page, A buys, B leaves.
- Descriptions: `MsgAbilityDescription` plus the ability id; a Djinni's is its
  ability (`ABILITY_DJINNI_FIRST` plus its number). Psynergy prices come from
  the PP cost (150 + 50 each); Djinn cost 500.
- Psynergy entries are ability icons, the chosen one swelling as in the shops;
  Djinn entries are the element's animated figure (see patch 8), the one under
  the hand drawn at full size.
- The overlay's list-grid screens and their shop data are removed. The Stats
  screen stays. The manager now calls `ArenaShop_Run` after the character strip.
- The shop item sub-menu uses the Attack icon for Weapons; the Equip icon did
  not draw in the arena.
- **Bank size:** the shop code is in bank `rom_main_06`, which had 114 bytes
  to spare and overflowed by about 2 KB (`cannot move location counter
  backwards` at `main.ld:72`). Bank 07's start moved from `0x080b5000` to
  `0x080b6000` for `tbs-en` (it had 5 KB free). Check slack with the map
  file when adding code to a bank.

### 10. Status panel and the stat counter
- Patch: `0010-Arena-status-panel-for-Characters-stat-upgrades-as-a-.patch`
- Files: `shop/shop/item_picker.c`, `scene/battle_arena.c`, `text/en.po`
  (`MsgArenaStatUp*`, `MsgArenaStatInfo*`, ids 10755 to 10766).
- Picker mode 3 (`ARENA_PICKER_STATUS`): `ArenaPicker_DrawStatus` repeats the
  Status screen's top rows (`ItemMenu_DrawMemberStatus` and the portrait from
  `StatusScreen_ShowMemberStatus`): portrait, class and "Normal" under it,
  name, level, experience, HP, PP, Attack, Defense, Agility and Luck. It is a
  copy, not a call, because `ItemMenu_DrawMemberStatus` reads the field menu's
  work and the shop's work holds the same bytes as something else. No coins
  window and no item grid in this mode; the Djinn rows are left out. Status
  conditions are not shown, only "Normal".
- `ArenaShop_Run` kind 2 sells the six stats: HP (+20), PP (+10), Attack,
  Defense and Agility (+5), Luck (+1). Each entry uses the icon of the item
  that raises that stat for good, `<stat> Up` for its name, a price tag, and a
  description "Raises X by n. Now m." (the two numbers are pushed with
  `MessageArgument_PushFar` just before the description is drawn). At a stat's
  cap the price window says MAX and a purchase does nothing. The overlay's list
  screens and their stat helpers are removed.
- No up-arrow glyph exists in the message font, so the names say "Up".
- The Characters picker is mode 3, Djinn 1, Psynergy 2; the counters are
  Psynergy 0, Djinn 1, Stats 2.
- Patch 12 centres the names on the Psynergy icons and Djinn figures in the
  picker panels. Tile text snaps to an 8-pixel row (a name at y + 4 drew at y),
  so a 16-pixel row puts the name at y + 8 and the icon at y + 4, as the Status
  screen does (`StatusScreen` preview lists: icon at +4, text at +8). The
  panel window is 11 tiles tall.
- Patch 11 (`0011-...`) removes the coins window from every panel mode (status,
  Djinn, Psynergy); only the old items mode, no longer used, still has it.

### 13. Saving through the Pause menu
- Patch: `0013-Arena-saving-through-the-Pause-menu.patch`
- Switch: `ARENA_PAUSE_MENU` (defined at the top of each file below; set to 0 to
  restore the original arena, where the Pause menu is unavailable).
- Files: `field/field_sequence/run.c`, `window/window/settings_menu.c`,
  `window/screens/save.c`, `scene/file_screen.c`.
- The Start (Pause) menu already has Save your quest, Sleep and Change
  settings. Two things shut it in the arena: the field answers
  `MsgFieldPauseUnavailable` when `FLAG_IN_BATTLE_ARENA` is set (`run.c`), and
  `PauseMenu_Open`/`PauseMenu_Choose` show only Change settings under that flag
  (`settings_menu.c`). Both are bypassed.
- Save is the game's own `Save_ToChosenFile` (file list, overwrite question).
  A save holds the whole game state, so base stats, Psynergy, Djinn, items and
  coins persist.
- In the arena `Save_ToChosenFile` sets `next`/`entrance` to the arena at
  `BATTLE_ARENA_FROM_FILE_SCREEN` and clears `FLAG_MONSTER_BATTLE` for the
  write, then puts both back. Without it a load enters with the last
  battle's entrance (`BATTLE_ARENA_AFTER_MONSTER_WIN`) and pays its reward
  again, or resumes the series.
- Loading: the title's Continue. New Game sets `restartScene` and
  `restartEntrance` to the arena, so Continue on a file from another build of
  the ROM (every rebuild is one) lands in the arena instead of at a Sanctum.
  There is no Battle option in this build's flow; New Game starts the arena.
- Not saved: the Monster Gauntlet rung, so a loaded game starts a new series.
- History: an earlier attempt put Save in the party manager's menu. A fifth
  icon made the prompt's message window open without its text (icons and
  message text appear to compete for the same VRAM cache slots; four icons were
  fine), and a second attempt gave it a person to talk to; both were dropped
  for the Pause menu. Keep icon rows to four.
## Planned

- Save and load the upgraded party.
- Stock arena text still mentions link cables.
- Stock arena resets the party to Isaac, Garet, Ivan and Mia on a save load.

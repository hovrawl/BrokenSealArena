# Gotchas (traps already hit)

## Build and tools

- `make ...; echo rc=$?` through `wsl` printed 0 on a failed build. Check the log
  for `***` and that `out/tbs-en/tbs-en.gba` has a fresh timestamp.
- After switching `~/alchemy` to a tree with different source files, `make` can
  stop with "No rule to make target ...c, needed by out/tbs-en/deps.mk": the
  generated `out/tbs-en/deps.mk` and `objects.mk` name the last tree's sources.
  Delete both (make rebuilds them). `try-upstream.sh` does this before each build.
- The whole build is in WSL's own disk (`~/alchemy`). Cloning or building under
  `/mnt/c` is slow and risks CRLF and file-mode problems.
- `build.ps1` cannot overwrite `build\tbs-en.gba` while an emulator has it open;
  it writes `tbs-en.new.gba` instead.
- PowerShell to bash quoting: backticks and `$(...)` in a `wsl -- bash -lc '...'`
  string, unquoted heredocs (`\n` becomes a real newline, backticks run commands),
  CRLF in PowerShell here-strings, and `wslpath` losing backslashes all bit. Use a
  script file.
- Do not name a PowerShell variable like a parameter (`$fresh` and `[switch]$Fresh`
  are the same variable).
- libmgba headers: do not add `-I/usr/include/mgba-util` (its `string.h` shadows
  the system one).

## ROM layout

- A bank of the main image has a fixed size. The shop bank (`rom_main_06`) had
  114 bytes spare; adding code overflowed it ("cannot move location counter
  backwards", `main.ld`). Bank 07's start was moved up 0x1000 for `tbs-en`. Check
  slack from `out/tbs-en/tbs-en.map` before adding code to a bank.
- A scene overlay can only call main-image functions that have a far-call stub and
  an `import` row (`system/overlay/imports.inc` plus the scene's
  `scene/import/<scene>.s`). Unexported functions need a new export in
  `gamepak/far_call/<BANK>.S`. Scene overlays have no string literals or static
  data of their own: use global `const` arrays.
- `gMenuWork` is shared: the shop's `ShopWork` and the field menu's work occupy the
  same block, so shop code must not call menu-bank functions that read the other
  layout (`ItemMenu_DrawMemberStatus`). Copy the drawing instead.
- Only `text/en.po` has the arena messages; the other editions do not build.
  Message keys must be contiguous from 0; new messages go at the end. Icon-menu
  labels are *consecutive* messages (`IconMenu_Center` takes a base).

## UI

- Canvas text (`Text_DrawString`, `Text_DrawNumber`) ignores
  `Window_ClearInteriorTiles` and uses a different, monospaced font; use the tile
  calls (`Text_DrawMessageAsTiles`, `Text_Draw*InWindow`) and messages for the
  game's font. Tile text snaps to an 8-pixel row: a name at y + 4 draws at y.
- An icon row of five or more left the prompt's message window without its text
  (VRAM cache pressure). Keep rows to four.
- `COMMAND_ICON_EQUIP` does not draw in the arena; `COMMAND_ICON_ATTACK` does.
- The Pause menu was shut in the arena in two places (`field_sequence/run.c`,
  `settings_menu.c`), hence `ARENA_PAUSE_MENU`.
- A Djinni's "sprite" in menus is its element's: sprites 90 to 93, animation 2.
  They must be placed every frame (`Render_ApplyProjectedPlacement`).

## Game flow

- Saving in the arena must reset `next`/`entrance` and the series flag for the
  write (and restore them), or a load replays the last battle's reward.
- Monster-series battles pay nothing in the stock game; coins here come from
  `BattleArena_RunRoundResult`.
- A formation has six sprite slots: a small enemy takes one, any other two.
- `New Game` ignores existing files; Continue loads one. There is no Battle
  option in this flow.

## Testing

- A stray A press beside a person starts their talk (or opens the field menu).
  Step with `tap A`, `shot`, and decide from the picture.
- Auto-battle flag poking (`0x16a`) did not win fights; mashing A does.

## Layout of upstream modules

- Some upstream objects are unity builds: `shop/shop.c` includes the files under
  `shop/shop/` ("Part of shop.c"), which share statics and `shop_internal.h`.
  New code for such a module goes in a new part file included from the parent,
  not in a new object. Check for "Part of ..." at the top of a file first.
- Scene enums such as `ACTOR_ATTENDANT` are defined inside the scene's `.c`, so
  a second file cannot see them: pass the value in, or move the enum to a header.
- Shell variables inside `wsl -- bash -lc '...'` called from Git Bash were
  expanded wrongly (a `git diff $B` came out reversed). Use literal values, or a
  script file.

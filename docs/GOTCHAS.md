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
  slack from `out/tbs-en/tbs-en.map` before adding code to a bank. The same error came
  from sprite data (four more sprite rows): the last region of `main.ld` now starts at
  0x08326000 and `build.ps1` pads to 0x08806000.
- A placement row's flag condition is only read when the actors are spawned. After
  changing the flag in the lobby, call `Event_SpawnActorPlacements(gFieldWork->tables[1],
  ACTOR_FIRST_PLACED)` again (it creates the new actors and resets the others' places).
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

## Arena flow

- The stock after-win spawn (`BATTLE_ARENA_AFTER_MONSTER_WIN`) is inside the
  circle, which starts the next fight at once ("Good luck!"); the stock Yes/No was
  the only gate. Anything that removes the question must also move the spawn.
- Starting a series sets `FLAG_BATTLE_ARENA_PLAYER_AGREED`; the stock flow clears
  it when a battle begins. Ending a series earlier must clear it, or the link poll
  (`BattleArena_PollPeerReady`) shows "The link was disconnected."
- A field message (`FieldMessage_ShowAtActor`) with two `{argument_signed_number}`
  blanks showed the first number twice ("Round 1 of 1"). Cause not confirmed; put
  the second number in the text and assert the constant.
- Scene temp flags (0x200 to 0x2ff) are written to the save raw, so a loaded game
  can start with one set that the live game had set. A file saved mid-series with
  `FLAG_MONSTER_BATTLE` cleared but `FLAG_BATTLE_ARENA_PLAYER_AGREED` set loaded
  into "The link was disconnected." Save state consistently: leave both as they are.
- The flag range decides what a save keeps: below 0x200 persistent; 0x200 to 0x2ff
  scene temp and 0x300 to 0x3ff area temp (cleared on a scene or area change).
  `FLAG_MONSTER_BATTLE` is 0x173 (persistent); `FLAG_MONSTER_BATTLE_WINS` (0x3f8)
  and `FLAG_AREA_TEMP_E8` are area temp, so keep real state in persistent flags or
  the saved struct (`linkTallies`).
- `MsgLobbyWonNumberBattle` uses `{plural_suffix}`: zero reads "You won 0 battle."
- `BattleArena_SaveMonsterBattleResults` writes into the current file with its own
  saving messages; after a New Game there is no current file. It is skipped.
- Isaac and Garet are created holding a **Machete**, and while it is equipped the battle
  draws them with their prologue sprites (the weapon is part of the sprite, no
  overlay). The prologue's end swaps it for an equipped Short Sword
  (`Party_EndChildhood`). Anything that skips the prologue (our New Game) must do
  the swap, or the party looks like the tutorial. `FLAG_CHILDHOOD` (class forms) is a
  separate thing and was not set.
- C89: a declaration after a `return` (or any statement) is a parse error in this
  compiler; put the early return after the declarations.

## Flags we claim

- Claimed persistent flags are listed in `module/arena.h`: so far `FLAG_ARENA_TOURNAMENT`
  (0x7f8, one byte). Before claiming another, check `ENEMY_DEFEATED_FLAG(classId)`
  (0x600 plus an enemy: 0x600 to 0x6ff are taken), the shop stock (0x400 plus a row),
  the Djinn, Psynergy tint and area-visited ranges below 0x200, and the named
  clusters; `flags.h` lists names only, and computed ranges are in macros and in the
  code (search for `FLAG_X +`). A byte flag must start at a multiple of 8.
- Boss rows in the ladder are enemy ids less `ENEMY_ID_FIRST` (8): Menardi is id 126,
  row 118. Large enemies take two of the six sprite slots.
- A boss pair at a low target level is still hard: pressing A does not win round 1 of
  the Boss Rush. Tests that need a win start as an easy team and switch the
  tournament byte after the battle begins.

- A program using libmgba's `struct mCoreThread` must be built with
  `-DENABLE_SCRIPTING` (the installed library has it): without it the struct is too
  short, the library overwrites the next field and the program crashes in
  `GBAFrameEnded`.
- PowerShell and Git Bash differ: a PowerShell tool call has no `grep` and a Bash one
  has no `Select-String`. Filter inside the shell the command runs in. And never pipe
  an empty heredoc to `python -`: it waits for input and the call hangs.

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

## The data port

- Run `port-reloaded-tables.py` once, on pristine tables: it assumes the source still holds
  the stock values (its `--check` says so by comparing its own rendering with the file). To
  redo it, `git checkout` the table files first.
- A table row that stock leaves out a field for (a zero) gets the field back only in struct
  order and only where the converter writes it; do not hand-edit a ported row and then rerun.
- The enemy rows have bytes 30 to 39 (reserved) the patch fills for bosses and Mimics. Not ported
  and not read by any code we decoded; if a boss ever misbehaves compared with Reloaded, look
  there first (`table-check.py` lists the rows).
- The class ward is `ClassDefinition.ward` (was `weakEffects[3]`); `weakEffects` is three
  bytes now, and the check that decides what ails a unit still reads three.
- Python written through an inline heredoc in this environment had `\r\n` turn into a real
  newline inside a string. Write scripts with the Write or Edit tools.

## Cups

- Cup data is generated from `scripts/cupdata.py`; do not edit the generated files in
  `~/alchemy`. The overlay (scene) and the battle code cannot share data, hence two outputs.
- Bank 07 of the main image was full: new data went to its own object in `rom_tail_00`
  (`objects.tsv`). Shifting bank starts in `main.ld` cascades to a "location counter" error.
- A test cannot win by mashing A against a cup's later rounds: start cup A, then poke the
  win count mid-battle (`cup_clear.txt`). Round 1 of a cup is tuned for the party's level,
  not for the stock-game damage (a level-8 target Vermin hit Isaac for 43).
- Python written through shell heredocs loses `\n`; write scripts with the Write tool.

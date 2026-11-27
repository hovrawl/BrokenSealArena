# Gotchas (traps already hit)

## Build and tools

- `make ...; echo rc=$?` through `wsl` (and the same can happen through MSYS2's bash) printed 0 on a failed build. Check the log
  for `***` and that `out/tbs-en/tbs-en.gba` has a fresh timestamp.
- After switching `~/alchemy` to a tree with different source files, `make` can
  stop with "No rule to make target ...c, needed by out/tbs-en/deps.mk": the
  generated `out/tbs-en/deps.mk` and `objects.mk` name the last tree's sources.
  Delete both (make rebuilds them). `try-upstream.sh` does this before each build.
- (WSL, before 2026-11-27) The build had to stay on WSL's own disk: under `/mnt/c` it was
  slow and risked CRLF and file-mode problems. With MSYS2 the work directory is on
  the Windows disk (`work/alchemy`) and that is fine.
- Windows, MSYS2: upstream's tools built by MinGW need binary stdio (`binmode.o`),
  a `rename` that replaces its target (two editions write the same asset at once:
  "write failed"), and a copy without `.exe` (make's directory cache does not see
  `ags-graphics.exe` as `ags-graphics`, so asset rules were silently skipped and
  the assembler said "file not found: ....gbapal"). `scripts/msys2/env.sh`.
- Windows, MSYS2: MSYS's `sha256sum` prints `hash *name`; upstream's source pins
  hash `hash  name` listings ("agbcc differs from pret/agbcc"). A wrapper in
  `scripts/msys2/bin`. The same message also came from the two symbolic links in
  `alchemy-gcc/agbcc/gcc_arm` checked out as text: they need Developer Mode, and
  `nativestrict` links need their target to exist, so they are made after the
  clone. Windows spells them `../x`, so `git status` calls the submodule dirty
  (`submodule.alchemy-gcc.ignore dirty`).
- Windows: Python, PowerShell's `Set-Content` and Git for Windows (`autocrlf=true`)
  all write CRLF. In the work directory, write files with `open(p, 'wb')` or the
  editor, and use MSYS2's git.
- `build.ps1` cannot overwrite `build\tbs-en.gba` while an emulator has it open;
  it writes `tbs-en.new.gba` instead.
- PowerShell to bash quoting: backticks and `$(...)` in a `wsl -- bash -lc '...'`
  (or `bash.exe -lc`) string, unquoted heredocs (`\n` becomes a real newline, backticks run commands),
  CRLF in PowerShell here-strings, and `wslpath` losing backslashes all bit. Use a
  script file.
- Do not name a PowerShell variable like a parameter (`$fresh` and `[switch]$Fresh`
  are the same variable).
- libmgba headers: do not add `-I/usr/include/mgba-util` (its `string.h` shadows
  the system one).

## ROM layout

- A bank of the main image has a fixed size. The shop bank (`rom_main_06`) had
  114 bytes spare; adding code overflowed it ("cannot move location counter
  backwards", `ld_script.ld`, formerly `main.ld`). Bank 07's start was moved up 0x1000 for
  `tbs-en`. Check slack from `out/tbs-en/tbs-en.map` before adding code to a bank. The
  same error came from sprite data (four more sprite rows): `RESOURCE_DIRECTORY_START` now starts at
  0x08326000 and `build.ps1` pads to 0x08806000. Patch 0044 overflowed bank 06 again (by
  0x81d): bank 07 now starts at 0x080b7000 and bank 08 at 0x080c9d00 (the banks after have no
  room: 08 ends within 0x2ac of 09). The bank starts are `#define`s at the top of
  `ld_script.ld`, one block per edition: English is the `#else` block. Patch 0055 (the UI
  kit) overflowed bank 06 again: every English bank from battle to the resource directory
  moved up 0x2000 together (battle 0x080b9000), which only needs room at the end of the
  image (it ends at 0x08805e76, `ROM_END` is 0x08806000). The next move needs `ROM_END`
  in `scripts/build.sh` raised first. `scripts/bank-slack.py` reads the map, but its bank
  edges are the old fixed ones: read the last object before each `*_BANK_START` instead.
- A placement row's flag condition is only read when the actors are spawned. After
  changing the flag in the lobby, call `Event_SpawnActorPlacements(gFieldWork->tables[1],
  ACTOR_FIRST_PLACED)` again (it creates the new actors and resets the others' places).
- A scene overlay can only call main-image functions that have a far-call stub and
  a row in `system/overlay/imports.inc` (`export Name, NameFar`; since upstream
  `a87775874b` each overlay's import table is derived from what it calls, so there is no
  per-scene list). Unexported functions need a new export in
  `gamepak/far_call/<bank>.s`. Scene overlays have no string literals or static
  data of their own: use global `const` arrays.
- `gMenuState` (was `gMenuWork`) is shared: the shop's `ShopState` and the field menu's state occupy the
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

## The native build (port/)

- It needs the GBA build first (`make tbs-en`): it reads `out/tbs-en/objects.mk`, the generated
  text and graphics, and the GBA ELF's `*CodeSize` symbols.
- Changing `GAME_CFLAGS` (say, adding a define) does not rebuild the objects: run with `-B`
  (20 seconds on four cores).
- The cartridge writes and reads through null pointers in a few places (the BIOS swallows
  them); natively that is a segfault. Fix each under `UBFIX` (the native build defines it),
  never by mapping page 0 (other platforms cannot). `gdb --args out/.../tbs-native --script X`
  gives the line.
- A routine the game copies to RAM runs there as a 7-byte jump back to the host code, so EWRAM,
  IWRAM and the stack are mapped executable (`-z execstack`). The native stand-ins for ARM
  areas the game copies into (e.g. `IwramSoundReverbCode`, 152 bytes a code) must be at
  least the cartridge's size, or the copy overruns the next global.
- Building or running downloaded code (SDL3 from source) is blocked in the cloud sessions;
  the SDL front end is checked there with `-fsyntax-only` against the SDL3 headers only.

## Flags we claim

- Claimed persistent flags are listed in `arena/arena.h`: so far `FLAG_ARENA_TOURNAMENT`
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

- Some upstream objects are unity builds: `shop/shop.c` includes `shop_run.c`,
  `shop_stock.c` and the rest beside it ("Part of shop.c"; before upstream
  `a87775874b` they were under `shop/shop/`), which share statics and
  `shop_internal.h`. New code for such a module goes in a new part file beside the
  parent, included from it, not in a new object. Check for "Part of ..." at the top
  of a file first. Our scene code is the same: `arena_boot.c` is included at the end
  of `file_screen.c`, `arena_menu.c` at the end of `battle_arena.c` and
  `arena_series.c` inside it, so they are in those overlays (there are no separate
  scene objects to place).
- Scene enums such as `ACTOR_ATTENDANT` are defined inside the scene's `.c`, so
  a second file cannot see them: pass the value in, or move the enum to a header.
- Shell variables inside `wsl -- bash -lc '...'` called from Git Bash were
  expanded wrongly (a `git diff $B` came out reversed). Use literal values, or a
  script file.

## The data port

- Upstream `a87775874b` rewrote the tables with designated rows (`[ABILITY_CURE] = {`)
  and upstream names for every value, and dropped the per-row name comments for
  abilities and items. `port-reloaded-tables.py` was written for the old positional tables;
  for that move the tables were regenerated from the old arena ROM's bytes (decode the
  stock and arena records by symbol, rewrite only the rows that differ, keep upstream's
  spelling of values, add designated rows for ids stock leaves blank). Do the same on the
  next upstream that reshapes them, and compare the built tables with the previous ROM.
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
- Bank 07 of the main image was full: new data went to its own object at the end of
  `.rom_tail` (a line in `ld_script.ld`, before `SPRITE_BANK_START`). Shifting bank starts
  cascades to a "location counter" error.
- A test cannot win by mashing A against a cup's later rounds: start cup A, then poke the
  win count mid-battle (`cup_clear.txt`). Round 1 of a cup is tuned for the party's level,
  not for the stock-game damage (a level-8 target Vermin hit Isaac for 43).
- Python written through shell heredocs loses `\n`; write scripts with the Write tool.

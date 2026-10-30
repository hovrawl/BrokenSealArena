# Decisions and why

- **Source patches over a pinned upstream submodule**, not xdelta/IPS/BPS and not
  a fork: upstream stays pristine, patches can be rebased and ported to The Lost
  Age. Binary patches only as a release format for players.
- **Route A for CPU teams** (data-driven formations of mixed existing enemies with
  `BattleEnemy_AdjustLevel`) rather than party-style units with new command AI:
  far less risk; Route B only if fights feel flat.
- **Menus built from the game's own parts** (icon row with a message prompt, the
  shop's strip, price tags and tooltips) over custom text screens; messages added
  to `en.po` so the font matches.
- **Saving through the Pause menu** (already has Save) rather than a custom
  person or the manager's menu; the arena-safe state is handled inside
  `Save_ToChosenFile`.
- **No Battle option on the title**: New Game starts the arena, Continue loads.
- **Headless testing on libmgba** because the installed mGBA 0.10.5 has no
  `--script` flag or CLI debugger.
- **Our code in our own files, upstream files only get hooks.** Spiked on branch
  `spike-newfile` of `~/alchemy` (two moves, both built and smoke-tested):
  `scene/arena_menu.c` (a new object in the 3cb overlay: one row in
  `objects.tsv`, a header, and ids passed in as parameters) and
  `shop/arena_shop.c` (a part file; `shop.c` includes it with one line, and
  `item_picker.c` is byte-identical to upstream again). Upstream's footprint in
  `battle_arena.c` fell from 134 lines to 46. Rule of thumb: a new object where
  the code is self-contained; where the module is a unity build (`shop.c` and
  its `shop/*.c` parts) add a part file; the hooks inside upstream functions
  stay as short edits that call into our code. See `docs/WORKFLOW.md` for the
  trial run that checks a new upstream.
  Result of moving everything (branch `spike-newfile`, full smoke suite looked
  at): our edits to upstream files fell from 1,320 lines in 19 files to 301 in
  17, 186 of them `text/en.po` messages. Our files: `arena_config.h` (the four
  switches, in one place), `module/arena.h` (what our files export to each
  other), `scene/arena_menu.c`, `scene/arena_boot.c`, `shop/shop/arena_shop.c`,
  `battle/battle/arena_ladder.c`, `window/screens/arena_icon_menu.c`,
  `window/screens/arena_save.c`. What stays an edit: the hooks (a call or two
  in `battle_arena.c`, `file_screen.c`, `formation.c`, `save.c`,
  `settings_menu.c`, `run.c`), the import and far-call table rows, one row each
  in `objects.tsv`, the bank start in `main.ld`, and `en.po`.
  The layered re-slice is done: `arena` is the seven-layer series (the old
  chronological one is `arena-chrono`).
- **Saves keep the tournament and rung; a series survives a break** (user,
  2026-10-30). Between rounds the player is never forced into the next fight:
  they can leave to heal, shop and upgrade and approach the gate again to
  continue. The first Gauntlet must not need max levels or classes. Djinn raise
  stats and change classes, a balance variable to test later. Levels are not
  designed yet. **Multiplayer 1v1 is the end goal**; how to get there (emulator
  linking, remote play) is an open research spike, see `docs/ROADMAP.md`.

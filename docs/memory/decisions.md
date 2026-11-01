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
  The layered re-slice is done: `arena` is the layered series (the old
  chronological one is `patches/tbs/` at commit `01a3234` in this repo; the spike
  branches in `~/alchemy` are deleted and their work is in `arena`).
- **Saves keep the tournament and rung; a series survives a break** (user,
  2026-10-30). Between rounds the player is never forced into the next fight:
  they can leave to heal, shop and upgrade and approach the gate again to
  continue. The first Gauntlet must not need max levels or classes. Djinn raise
  stats and change classes, a balance variable to test later. Levels are not
  designed yet. **Multiplayer 1v1 is the end goal**; how to get there (emulator
  linking, remote play) is an open research spike, see `docs/ROADMAP.md`.
- **Attendant, loss and 1v1** (user, 2026-10-30): the attendant shows the current
  menu when no Gauntlet is running and a Yes/No "give up?" when one is. A loss
  ends the whole series, no retry; the player goes to the counter. 1v1 is **4v4**
  (the stock link exchange is three a side, so the protocol must grow to four).
- **Interfaces are finalised before Gauntlet design**, from written reusable rules
  in `docs/UI.md`: reuse existing screens and their parts first, text is always a
  message, fill in the spec template and review it before code.
- **Series outcomes** (user, 2026-10-30): giving up is not a loss (the stock game
  tallies losses in `gMainRoutineWork.linkTallies[LINK_TALLY_MONSTER_LOSSES]`;
  keep that for real losses; giving up keeps the best streak). Rung 12 cleared is
  a win and ends the series. The heal after each win stays (a future difficulty
  modifier may skip it, probably per tournament). After a loss the party is
  restored to full and the standard spawn is used. Roadmap later: post-battle
  events (per win, tournament win, bespoke loss), a proper tournament win, and
  fight data (log every action, derive damage by character, type and element).
- **Spare save bytes are a future option, not a task** (user, 2026-10-30): story-only
  persistent flags and, after the Lost Age decomp shows what its transfer reads, the
  struct's unnamed bytes could hold per-gauntlet stats later. Repurpose, never shrink.
  Fight logs are kept in memory per round, not saved. See `docs/ROADMAP.md`, "Later".
- **Tournaments are data plus a persistent byte** (2026-10-30): the tournament of the
  running series is `FLAG_ARENA_TOURNAMENT` (0x7f8, a byte flag found by scanning every
  computed flag range; claimed flags are listed in `module/arena.h`). Rounds, ladder,
  messages and healing are per tournament (`ARENA_ROUNDS`, `ARENA_HEALS`). The Boss
  Rush (six boss rounds, no healing) exists to test that logic; its balance is data and
  is deferred with the Gauntlet's. The user chose to skip the balance pass until the
  logic is tested.
- **Multiplayer** (user, 2026-10-31): Broken Seal 1v1 is **4v4**, bespoke story
  characters only. The Lost Age has eight characters with party switching; whether to
  fix the first row of four is undecided. First build **offline records**: send your
  party's record and let the game play it as an AI opponent (pseudo-online); real-time
  play is a separate step, in increments. The spike (`docs/MULTIPLAYER.md`) showed two
  hack instances link and fight locally, and that 4v4 needs the opponent's Djinn table
  moved out of enemy unit 3.
- **Multiplayer baseline** (2026-10-31): the stock link battle is real time and player
  driven (each console sends its own chosen actions over the link; the enemy AI is not
  used). Online play therefore rests on the emulator carrying the link cable. Records
  plus an AI opponent is a later fallback, not the plan. Next: investigate 4v4.
- **4v4 hits the sprite VRAM limit** (2026-10-31): at link-battle target selection the 512
  blocks of sprite VRAM (32 KB) are 94 percent used; eight 64-block character sprites need
  all of it, so one (the party's 4th) is evicted and the 4th opponent flickers. Roughly 30
  blocks short. See `docs/MULTIPLAYER.md`. The data and exchange work at 4v4; the picture is
  what does not fit.
- **Psynergy is learnt by class, not bought** (2026-11-01): the base game's own mechanic is
  kept: the Djinn a character has set decide the class (Venus-only Djinn lead down the
  Squire line and so on), the class limits the Psynergy pool, and each Psynergy has a
  level requirement on top; it is not permanent, which is liked. The data is in
  `gClass_DefinitionTable` (`abilities`, `required`) and `Unit_RefreshPsynergy`; see
  `docs/PROGRESSION.md`. The party manager's Psynergy shop contradicts it (not decided what
  replaces it). The forum rebalance mod and its spreadsheets are saved there as reference
  only, not to be taken to heart.
- **Reloaded rebalance is ported into our source, not patched on** (2026-11-01): engine
  changes by hand in our own files behind switches; data changes generated once from the
  IPS (`scripts/ips-table-diff.py`) into our tables and committed as ordinary patches. The
  patched-stock-ROM oracle test is optional (not wanted). The owner will tell the authors;
  credit them. Their files stay in `reloaded/` (git-ignored). Order: rules, ailments,
  abilities and classes together, items, then enemies, Djinn, characters, text. See
  `docs/RELOADED.md`.
- **Reloaded engine rules on by default; new games start at level 50** (2026-11-01): the
  `ARENA_RULES_*` switches default to on (they run over the stock tables until the data is
  ported). A New Game levels the party to 50 (`ARENA_START_LEVEL`) so every class's Psynergy
  is open and only the set Djinn limit the pool. Balance against the ladders (rungs top out
  at level 45) is deferred.
- **Progression by cups** (2026-11-01): the game is a battle simulator, not a story replay.
  Cups are linear and mimic story regions (mobs from an area, capped by its boss); a cup sets
  the party's level (bracket of ten, the first can be level 10) and finishing it unlocks the
  next gate, Djinn and items. Side cups (themed, mechanic-challenge, the Boss Rush) sit beside
  the line. The stat shop is for level 99 only. 4v4 PvP has two brackets, a cap of 50 (standard)
  and 99 (tuned builds), player's choice. See `docs/CUPS.md`.
- **Reloaded design intent kept** (2026-11-01): summon turn gating, no unleashing while
  deluded, luck 40 immunity and the ward are intended, per the author's post
  (`docs/RELOADED-DESIGN.md`). The lobby signature is `BSR4` so builds with different rules
  do not link.
- **Cups are data; the level is an unlock** (2026-11-01, revises the cups entry): a cup does
  not set the party or its level. New Game starts at level 10 with the first cup only; the
  first win of a main cup plays an event scene announcing the unlocks (the next level, Djinn,
  shops, cups); older cups stay playable over-levelled. 10-50 is the base progression, 50-99
  open-ended (an endless run later; Crossbone Isle as a post-game model). The Psynergy shop is
  retired; the stat shop stays and Luck/ailments are to be explored separately. See
  `docs/CUPS.md` and the revision at the top of `docs/CUP-SPEC.md`.
- **Cup details** (2026-11-01): the Monster Gauntlet is retired and the Boss Rush is one of the
  first extra cups, after the base progression; a cup start changes nothing about the party;
  start purse 1500 coins; the first-clear reward is gear tied to the cup's region; cups are
  named by place, one per boss early and grouped later; regions with no story boss are capped
  by their Djinn battle. See `docs/CUP-SPEC.md` (revision).
- **Five main cups (proposal, 2026-11-01)**: bosses grouped by level into five cups (Tret; Saturos
  and Killer Ape; Hydros and Manticore; Kraken, Toadonpa and the Lizards; Saturos, Menardi and
  the Fusion Dragon), party level before each 10, 20, 30, 40, 50. Deadbeard/Crossbone Isle is
  the first post-game challenge; the caped strangers are too strong an opener. See
  `docs/CUP-SPEC.md`.
- **Seven main cups, levels follow the enemies** (2026-11-01, revises the five-cup proposal): Saturos
  and Killer Ape are single-boss cups; the old level-40 cup is split in two; the party level need not
  always rise (a cup's reward is Djinn and shop stock, from Reloaded's shop list); levels follow the
  enemy levels (a 5-level award is allowed). See `docs/CUP-SPEC.md` (revised proposal): Tret, Mercury,
  Mogall, Altin, Tolbi, Lunpa and Lighthouse cups; Crossbone Isle post-game.
- **Gear rewards come from the dungeons** (2026-11-01): the seven cups and their level disparity are
  accepted (Djinn carry the power balance; cup F's seven Djinn at once is fine). Gear that the story finds in
  chests is the reward: given **mid-cup, the first time a round is reached**, so it can be equipped for
  the next fight, and off-path chest gear is earned in side cups themed on a dungeon. Shops sell
  Reloaded's shop list. A script (`scripts/cup-gear.py`, to write) joins scene, chest and item.
- **Djinn in cups** (2026-11-01): a cup may include its region's Djinn fight as a round (one or two) and
  end by giving a Djinni, so not every Djinni is bought: each is fought, given or sold once its cup
  is cleared. Cup party levels are our own proposal anchored to enemy levels, which Reloaded barely
  changes (13 of 165 rows, by 1 to 3); it changes the enemies' stats instead.

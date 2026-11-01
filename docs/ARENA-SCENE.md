# How the arena scene and the file list work: notes for trophies, cup NPCs and the file display

STATUS 2026-11-01: built in patches 0032 to 0036 (trophies, champion and scout, file list cups, 16 x 16 trophies, display cases in the lower wings); see CHANGES 32 to 36. Depth rule: actors sort by z in steps of about 8 pixels; `height` lifts a picture without changing the sort (CHANGES 36).

Research read from `~/alchemy/games/tbs` on 2026-11-01 (read-only, while the cup spec agent
works), to be moved into the docs after that branch is merged. Nothing here is built.

## The arena scene (the Battle Arena lobby)

- A place is a **scene**: one row of the scene table whose code is an **overlay** unpacked on
  arrival. The Battle Arena's is `src/scene/battle_arena.c` (plus our `arena_*.c` files). The
  field sequence only asks the scene six questions through an entry table (`scene/README.md`
  explains them): where the party arrives, who stands where, where it can leave, what each
  talk or step starts.
- **Where the party arrives:** `gBattleArenaEntrances[]` (rows of entrance id, condition, x,
  y, z, facing, camera numbers). Our rows set the spawns after wins and from the file screen.
- **Who stands where:** `gBattleArenaActorPlacements[]` (21 rows, 24 bytes each: sprite id,
  **condition**, movement type, x, y, z in 16.16 pixels, facing, talk facing, flags).
  `BattleArena_SelectActorPlacements()` returns this table, or
  `gBattleArenaBattleActorPlacements[]` after a defeat (the people trade places with the
  visitors), so **the scene already picks a table in code**. The rows are numbered by
  `enum BattleArenaActorId` (attendant, the manager, the healer, the greeter, the visitors,
  the debug helper...), and the talk triggers refer to those numbers.
- **The condition field is the hook for "different NPCs by cups earned":** a row can be
  `CONDITION_ALWAYS`, `IF_FLAG_SET(flag)` or its clear form. The stock rows for Garet, Ivan,
  Mia and Jenna already use it (`IF_FLAG_SET(0x1)` and so on). So an NPC (or an object) that
  appears once a cup is cleared is **one more row with `IF_FLAG_SET(cup flag)`**, no code,
  as long as the flag is persistent (below 0x200 or 0x400 and above, see GOTCHAS: 0x200 to
  0x3ff are cleared).
- **What a new NPC costs:** a placement row (a sprite id, a place), a talk handler (a C
  routine in the scene overlay, started by a trigger row; messages in `text/en.po`), and
  sprite memory: field sprites are drawn from the same sprite VRAM cache that limited 4v4
  (512 blocks), but the lobby has few distinct sprites, so there is room. The overlay has a
  size limit (the arena overlay is object `3cb`; `objects.tsv`).
- **Physical cups (trophies) in the room:** three routes, in order of effort:
  1. **Actors:** place an actor with a sprite that looks like a trophy, statue or chest, with
     a "stand" movement and no talk (or a talk that opens the cup list): one row per cup,
     each `IF_FLAG_SET` its cup's flag. Needs a suitable existing sprite (the sprite table
     `sprites.tsv`, 513 rows, many field objects; to be searched for trophies, banners,
     statues, medals) or a new one (the sprite pipeline we used for the 32x32 opponents:
     a PNG sheet plus a row in `sprites.tsv` and `layout.tsv`).
  2. **A "trophy case" actor** that shows the cups in a window when talked to (cheaper, uses
     our icon-menu rules in `UI.md`).
  3. **Map tiles:** the arena map is baked data (a tile map and collision for the room);
     drawing trophies into the background means editing the map graphics (and a second map
     for the cups-earned variants), which is much more work. The actors route avoids it.
- Where the NPCs stand matters for the existing lobby: collision and the spawn in the circle
  (see the entrances), and the linked-battle spots.

## The save file list (where the Djinni overlay is)

- The file list (Continue, and our Pause-menu save) shows, per file, a **summary record**
  `struct SaveFileSummary` (`include/system/save.h`): the leader's name, level and class,
  play time, area, coins, **`u8 djinn[4]` (the party's Djinn of each element)**, the party,
  a flag count and window colours. It is built when saving by `Save_BuildFileSummary()`
  (`src/window/screens/save.c:163`; the four counts from `Party_SumDjinnCountsFar(element)`
  at lines 201 to 204).
- It is drawn by `FileList_ShowDjinnSprites` (line 678: **four Djinn sprites, one per
  element, in a row**), `FileList_PlaceDjinnSprites` (the task that positions them each
  frame) and `FileList_DrawDjinnCounts` (line 747: two-digit counts, 24 pixels apart, row 16
  of the file's window). That is the "Djinni overlay section".
- **To show cups instead:** keep the four-slot shape, store in `djinn[4]` (rename it) the cup
  progress (for example one byte per tier of four, or a count per bracket; or four bytes of
  cup bits, 32 cups), and replace the four element sprites with four trophy sprites (lit when
  earned, or counted). The two draw functions and the build function are all in
  `window/screens/save.c`; the same code serves the title-screen Continue and our save, so
  one change covers both. Older saves would show their old Djinn counts as cups: new saves
  only, which matches the New Game policy.
- Costs: new art for four trophy sprites (or reuse four existing item or medal icons first),
  the meaning of the four bytes, and a text row if a label is wanted.

## Suggested agent task after the cup framework (one agent, own branch)

"Arena dressing": (1) search the sprite table for trophy-like sprites and pick or make
them; (2) add cup-flag-conditioned placement rows for trophies and one cup-themed NPC per
bracket, with talk lines; (3) replace the file list's Djinni display with cups; (4) a
smoke test per state (no cups, some cups, all cups) with screenshots of the lobby and the
file list. The cup framework's unlock flags (see the cup spec) are what these rows read.

## Owner's decisions (2026-11-01)

- **Own trophy sprites:** make them (a PNG sheet through the sprite pipeline, as the 32x32
  opponents were). Placeholder art can be generated by a script first, then redrawn by hand.
- **Existing saves are not supported** (new saves only), so the file summary's meaning can
  change freely.
- **The number of cups is undecided**, possibly more than four. If more than four, the file
  display pages through them (L and R moving down the list); not a priority yet. To check
  when built: which buttons the file list already uses, and that L and R are free there.

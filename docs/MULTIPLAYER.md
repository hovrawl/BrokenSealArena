# Multiplayer: the spike

Findings from reading the link code and running two linked copies of the hack
(2026-10-31). The goal (`docs/ROADMAP.md`, Phase 4) is a 1v1 between players with
four characters a side. This file records what is true, what was tried and what is
still unknown, and recommends a route. **Nothing in the patches changed**: this is
research plus a two-console test driver.

## Decisions it rests on (from the user)

- **Broken Seal: 4v4.** The party is the four story characters (Isaac, Garet, Mia,
  Ivan). No characters outside the bespoke ones.
- **Lost Age** has eight characters with party switching. Undecided whether to
  disable switching and fix the first row of four. Either way the characters are
  the story's own, so the record format only ever holds those.
- **Offline records first.** Support sending your party's record, and have the game
  play it as an AI opponent ("pseudo online"). Real-time play is a different and
  separate step, tested in increments.

## What the stock game does (read from the source)

The Battle Arena already has a linked battle (`scene/battle_arena.c`,
`battle/battle/link.c`, `turn.c`, `run.c`). The flow:

1. Each player talks to the attendant and applies ("Would you like to apply?").
   The link poll (`BattleArena_PollPeerReady`) watches the other console's
   signature through the serial transfer (`gLinkPeerSignatures`).
2. Both step into the circle. `BattleArena_ExchangePartyRecords` swaps the parties:
   **three** `struct Unit` records (`LOBBY_UNIT_RECORD_COUNT` is 3), 0x154 bytes
   each (the 0x14c unit and 8 more), then the **Djinn recovery table** (0x140 bytes).
   The order depends on which console is the parent.
3. The opponent's records are received in place into the battle's **enemy units**
   0x80 to 0x82, and each name gets "Enemy" in front (the battle shows
   "EnemyIsaac appeared!").
4. The battle runs as normal. Each turn, `LinkBattle_SyncTurn` handshakes both
   consoles through a fixed sequence of signatures, the two sides' chosen actions
   are exchanged (`LinkBattle_SendActions`/`ReceiveActions`), and both run the same
   random seed, so both consoles compute the same outcome.

So a record is a **whole `struct Unit`**: base stats, level, items, equipment,
Psynergy, Djinn held and set. Whatever the party manager changes travels with it.
(Checked by reading the structure; the in-battle effect of each field was not
tested.) The Djinn recovery table is the party's `gMainRoutineWork.summonMask`
block.

## Baseline: the stock link battle is real time and player driven (confirmed)

Read in `battle/battle/turn.c` (`Battle_GatherActions`, `Battle_AppendLinkedActions`):

- Each turn, each console builds **its own party's** actions from the player's command
  menu (`Battle_BuildUnitActions`).
- In a link battle (`isLink`) the enemy AI is **not called**: where a normal battle
  does `Battle_BuildOpponentActions` (which runs `BattleAI_ChooseAction`), a link battle
  does `Battle_AppendLinkedActions` instead, which **sends this console's actions over
  the serial link and receives the other player's**. The received actions become the
  opponent's, with their targets flipped to this console's point of view.
- The consoles stay in lockstep: the parent sends first and gives the turn its random
  seed, the child checks both agree on the next random number, and `LinkBattle_SyncTurn`
  and `LinkBattle_WaitSync` handshake before and after every action. Both consoles
  compute the same battle.

So the link is the "online" part: if the emulator carries the link cable between two
players, the game needs no change for real-time play, and the AI is not involved. This
is the baseline for the rest. The records-plus-AI route below is a **fallback for
later**, not the plan.

**Observed too (2026-10-31, `link_turns_*.txt`, `link_psy_*.txt`).** Both consoles
issued real commands and the actions crossed the link:

- An Attack turn: one console shows "Mia attacks! EnemyGaret takes 34 damage!" then
  "EnemyGaret attacks! Garet takes 30 damage!", the other player's Garet answering.
- A **Psynergy** turn (command row: Fight, then Right to Psynergy, A, pick, A, target):
  Isaac casts Ragnarok (PP 7). One console shows "Isaac casts Ragnarok! EnemyGaret takes
  79 damage!!!" with Isaac's PP 84 to 77; the other shows "EnemyIsaac casts Ragnarok!
  Garet takes 79 damage!!!" with Garet 300 to 221. **Both agree on the 79**, so the shared
  random seed and the lockstep hold for Psynergy as well.
- The command layout, for scripts: the top row is Fight, Flee, Item; Fight opens
  Attack, Psynergy, Item, Defend. (Djinn and Summon rows appear once Djinn are set.)

## What was tried

`scripts/smoke/link.c` runs **two ROM instances linked by libmgba's own lockstep
link**, each running a smoke script, with a loose frame barrier so the two stay in
step. It follows the lockstep callbacks of mGBA's Qt multiplayer controller. It is
built with `-DENABLE_SCRIPTING`, because the installed library is (without it the
thread struct is too short and the program crashes: see GOTCHAS). `link.sh` builds and
runs it; `link_battle_0.txt` and `link_battle_1.txt` are the two consoles' scripts.

Result, shown in `build\smoke\link_battle3.png` (not committed):

- the link comes up (`gLinkStatus` reads 3 in its low bits on both consoles, and the
  arena's link-up flag is set);
- the stock handshake works between the two copies: Multiplayer, "Would you like
  to apply?", Yes, "You have asked for a battle";
- both step into the circle and **a real linked battle starts**: each console shows
  the other's party as "EnemyIsaac", with three a side (Isaac, Garet and Mia).
  **Ivan is left out on both sides, the stock three-a-side limit.**

## What the recovery tables are

In a battle, a Djinni can be **set** (giving its character stats), then spent: used for
its attack it goes to **standby**, and a standby Djinni is then used for a **Summon** or
**recovers** over a number of turns and is set again. The game tracks this in a
**Djinn recovery table** for each side (`struct DjinnRecoveryTable`, 268 bytes):

- `summonMask` (4 bytes): which Summons are available this turn;
- one more word (the party's table has the coins here, "not named");
- a **list of up to 64 entries** plus a count. Each entry (4 bytes) is one Djinni on
  standby or recovering: its element, which Djinni, **which unit it belongs to**, and the
  turns until it is set again.

It is what the Djinn menu in battle reads ("which Djinn can I use, which are
recovering"), what Summon availability is computed from, what ticks down at the end of a
turn (`DjinnRecovery_CountDown`), and what battle setup fills when the Djinn a unit has
set are put on the field. The party's own table is a block inside the saved game state
(`gMainRoutineWork`, from byte 12, which is why the first word is `summonMask` and the
second is the coins: the table overlays the start of that struct).

**In a link battle each console needs the other's table too**, because the opponent's
Djinn are theirs to use and their recovery must be shown and ticked the same on both
screens. So after the units, each console sends its table, **with each entry's owner
renumbered** to the number the other console gives that unit (0x80 plus its place) and the
entries of units not sent removed (`BattleArena_SendPartyRecords`). The receiver stores it
as the "enemy side's" table. **There is no separate place for it: it is written over a
battle unit record** (`Djinn_GetRecoveryTable(1)` returns `Unit_Get(FIRST_ENEMY_UNIT + 3)`),
and the stock game can only do that because a link battle looks at the opponent's first
three units and never at the fourth.

## Answers to the four questions

1. **Can two copies of the hack link on one machine?** **Yes.** Proven above, with
   no change to the ROM. A linked battle can be scripted and screenshot like any
   other flow. (Not yet driven through to a result; see "Next steps".)
2. **Over the internet?** **Not tested, and not answerable here.** Emulators link
   only locally. The link needs both consoles stepped in lockstep (the sync
   handshake waits for the other side every action, tolerating about
   `LINK_MAX_MISSED_FRAMES` missed frames), so a live game over the internet means a
   relay or netplay layer that carries the serial traffic between two emulators with
   latency. That is the hard part and a separate project; the offline route below
   avoids it.
3. **Do the records carry what the shop changes?** **Almost certainly yes**: the
   whole unit is sent. To confirm in a test, change a stat in the manager on one
   console and check it on the other's enemy unit. Not done yet.
4. **How hard is four units?** **Moderate, with one real obstacle.** What a 4v4
   needs, all from the code:
   - the send and receive loops (3 to 4) and `LOBBY_UNIT_RECORD_COUNT`;
   - `BattleArena_CopyPartyOwnerIds` caps the party list at 3, and
     `LINK_PARTY_SIZE` (in the battle's own link code) is 3;
   - **the obstacle:** the battle allocates exactly **six** enemy units
     (`ENEMY_UNITS_SIZE` is 0x7c8, six of 332 bytes, units 0x80 to 0x85), and the
     opponent's **Djinn recovery table is stored in unit 0x83** (`Djinn_GetRecoveryTable(1)`
     returns `Unit_Get(FIRST_ENEMY_UNIT + 3)`). A fourth opponent unit would be 0x83
     and collide. The fix is to move the table to 0x84 or 0x85, a change to
     `Djinn_GetRecoveryTable` and its far-call users;
   - each packet is 340 bytes and the receive writes 8 bytes into the next unit
     (the next packet rewrites it), so four units fit, with the table moved;
   - **sprite slots are not a problem** (corrects an earlier guess): the six enemy
     *sprite slots* are for monsters. A link opponent is a character (`classId` set), drawn
     by `BATTLE_CHARACTER(...)` in `placement.c`, and `BattlePlacement_LayoutEnemies` places
     any count (it has a case for four or fewer).
   - **both consoles must run the hack**: a hacked game's exchange will not match a
     stock one's.

## 4v4 prototype (2026-10-31, branch `link4` in `~/alchemy`, not exported)

The table can be **offset**, and four a side works. Behind a new switch `ARENA_LINK4`
(`arena_config.h`, default on), the changes are small (24 lines in four upstream files):

| File | Change |
|---|---|
| `battle/battle_internal.h` | `LINK_PARTY_SIZE` 3 to 4 (the battle's party limit in `BattleParty_PrepareMembers`, and the number of opponent units `BattleEnemy_List` scans) |
| `scene/battle_arena.c` | `LOBBY_UNIT_RECORD_COUNT` 3 to 4; the receive loop (`slot > 2`) and the send padding loop (`i <= 2`) use it; `BattleArena_PartyContains` allows four |
| `game/game/units.c` | `Djinn_GetRecoveryTable(1)` returns unit `FIRST_ENEMY_UNIT + 4` instead of `+ 3` |

The battle holds six enemy units (`ENEMY_UNITS_SIZE` is 0x7c8, six of 332), so units 0x80
to 0x83 are the four opponents and the table takes 0x84, with room to spare (the table's
320 bytes fit in one 332-byte unit).

**Result** (`link_turns_*.txt`, two consoles): the HUD shows Isaac, Garet, Mia and Ivan;
four characters stand on the opposing side; the intro names them ("EnemyGaret appeared!
EnemyMia appeared!"); and turns run, with mirror lines agreeing ("EnemyIvan attacks! Garet
takes 13 damage!" and "Ivan attacks! EnemyGaret takes 13 damage!").

**Correction (same day): the first screenshots showed 4v3.** I called it 4v4 from the
pictures, and the data was right but the picture was not. Read from memory on both
consoles (`peekp`, the opponent units at `gEnemyUnits`): units 0x80 to 0x83 are Isaac,
Garet, Mia, Ivan, all side 2 with HP 287, 300, 220, 188, and unit 0x84 is the table
(side 0). So it was **four opponents, but only three drawn**: the stock enemy layout
spaces characters 38 pixels apart from z 45, which puts a fourth at z -69, off the end of
the line. Fixed in `battle/battle/arena_link.c`: with four link opponents they stand where
the party's four stand, mirrored (x -80, z 48, 16, -16, -48). After the fix all four are
visible on both consoles (`link_view_*.txt`).

**Full linked 4v4 to a result (`link_full_*.txt`).** Both consoles mashed A through a whole
battle: Stun Voltage, Garet stunned, party members falling, and a winner. One console ended
with Mia at 220 and Ivan at 1 HP and the arena's wins board at 001; the other ended with Isaac,
Garet and Ivan down and Mia defeated, then the loser's flow ("Battle results were saved." and
Garet: "We need to work on our teamwork. Let's try harder next time!"). Both consoles agreed
on the outcome. **Caveat:** "Battle results were saved." is the stock link flow writing a record
into the current save file (`BattleArena_SaveBattleResults` calls `Save_ProcessSelectedFile`);
after a New Game there may be no current file. Not investigated; it is skipped for the monster
series already (patch 8), the link flow still does it.

**Watch item from the user: EnemyIvan looks off at target selection** (screenshot: Ivan stands
apart from the other three, higher up the frame, in a back view). Investigated with bursts of
frames 7 apart while choosing a target, zoomed crops, and a party-order swap:

- With the opponents at z 48, 16, -16, -48 (mirroring the party), the fourth place was
  **clipped at the right edge** (a hard vertical cut where the arena wall is) and EnemyIvan
  vanished from some frames. Fixed by pulling the line in and left: z 45, 21, -3, -27 now,
  after trying 36, 12, -12, -36; nothing is clipped.
- **Still open:** with the normal order (Isaac, Garet, Mia, Ivan), EnemyIvan in the fourth place
  **alternates between two views** while the cursor sits on Garet: a back view (green cloak,
  arm out) standing apart to the right, and a front view (red jacket, staff) next to Mia. The
  other three never change. **With the order swapped (Ivan third, Mia fourth) Ivan is stable
  and front-facing in every frame**, so it follows Ivan being the fourth, not the layout.
  Cause not found. Candidates: his enemy-side battle sprite (stock link battles never had him
  fourth), or the target highlight's pulse acting on a fourth unit (the pulse is on the
  selected Garet only), or the per-frame sprite priority update treating the fourth enemy place
  specially. Next step: read `BattleObject_UpdateSpritePriorities` and the highlight code for
  anything indexed by enemy place, and compare against a monster formation with four enemies.
- It is not an OAM overflow: 11 of 128 sprite entries were drawing at target selection.

**Chased down (2026-10-31): the cause is the sprite VRAM budget.** What was measured, in
order (all with the two-console driver's new `peekp`, `peekpp` and `peekp3` reads):

1. EnemyIvan's actor never moves (x -80, z constant) and his facing is constant (all four
   opponents face within a few degrees of straight on), so it is not geometry or turning.
2. The four opponents' battle objects are identical in shape: resources 300 to 303, the same
   palette (1), scale and shadow. Removing every opponent's weapon overlay did **not** stop
   the flicker (tested and reverted), so it is not the overlays.
3. Their `Sprite` records are identical and unchanging in every frame: cache slots 4, 5, 6, 7
   (Ivan is 7), width 64, the same animation number, `dirty` 0, three layers.
4. **The VRAM block table at target selection** (`gVramCacheBlockOwners`, 512 blocks of 64
   bytes, the whole 32 KB of sprite memory): the opponents' entries 4 to 7 and the party's 0 to
   2 are resident at **64 blocks (4 KB) each**; **entry 3, the party's fourth, is missing**;
   entries 8, 9 and 10 (the target markers and the like) hold 16, 8 and 4 blocks; 2 more
   blocks belong to entry 93; **34 blocks are free**. A resident entry 3 would need 64, so the
   cache is **about 30 blocks over budget**.

So: eight full-size character sprites need 8 x 64 = 512 blocks, which is *all* of sprite
VRAM, leaving nothing for the cursors, windows and status icons that a battle also needs.
The stock game never gets there (a link battle has at most six characters, 384 blocks; a normal
battle has four characters and monsters). The game copes by evicting an entry, and the loser is
the last one loaded. The party's Ivan and the opponent's Ivan use the same resource (302), so
they share the cache's idea of that sprite, which fits Ivan's front view (opponent) and back
view (party) taking turns in the same tiles. I did not prove that last step (it needs the
OAM entries and the tile contents at a flip), but the budget itself is measured, and it
explains why only the last-loaded character misbehaves and why a swap of the order moves
the problem to whoever is fourth.

**What this means for 4v4**
- It is a hardware limit, not a bug in the layout code: 32 KB of sprite memory cannot hold
  eight 4 KB characters plus the UI. Anything that keeps all eight at full size needs about
  30 more blocks.
- Ways to find them (not tried): free the UI sprites for the duration of the link battle;
  make the opponents' sprites cheaper (the entry is 64 blocks because the frame is 64 x 64 at
  one byte a pixel, so a smaller frame or 4 bits a pixel would halve it, but that is art and
  engine work); let the party and the opponent share one set of tiles per character (not
  possible as is, since one is seen from behind and the other from the front); or draw the
  fourth opponent differently (a smaller sprite, a simpler picture).
- Test of the diagnosis, worth doing first: a 4v3 (four of ours, three of theirs) should fit
  (7 x 64 + 28 = 476) and Ivan should be stable. That is the stock limit plus one.

**What a sprite costs, and the shrink test (2026-10-31).** Read from the ROM
(`gBattleSprites` rows and `gSprite_AnimationMetadata`, width x height / 64 bytes):

| Frame | Blocks | Who |
|---|---|---|
| 64 x 64 | 64 | the four characters (resources 300 to 303, both sides) and **117 of the 172 enemy classes**, every large monster and boss |
| 32 x 32 | 16 | the other 55 classes (43 of them the "small" ones that share a slot) |

- A battle has six enemy sprite slots; a large enemy takes two, so a stock enemy side costs
  at most 3 x 64 = 192 blocks (or 6 x 16 = 96 small). With four characters (256) the worst
  stock battle is about 450 blocks plus the UI's 30, which fits. That is why "more than four
  enemies" is fine: the budget is blocks, not heads. Four a side is 512 before any UI.
- **Weapon overlays cost nothing extra.** The body, weapon overlay and shadow are layers of one
  `Sprite` that are composited into the unit's own frame; the table shows exactly one 64-block
  entry per unit (plus shared entries 8, 9, 10 and 93 for markers and shadows). Removing the
  opponents' overlays earlier did not change the flicker, which agrees.
- **The shrink test.** A throwaway change gave only the fourth opponent a 32 x 32 sprite
  (resource 453, a Bat). The block table then showed entries 0 to 6 at 64, entry 7 at 16, and
  **entry 3, the party's Ivan, resident again** with 18 blocks free. So the budget really is
  the cause. (Reverted; the visual is not a fix.)
- **Implication for a real fix.** The opponents are the ones to make cheap: they are drawn
  at 1.3 x scale anyway (enemies are), and a 32 x 32 frame for each of the four opponents
  costs 4 x 16 = 64 blocks instead of 256, leaving about 190 free. That needs 32 x 32
  versions of the four characters' battle pictures (new resources and metadata rows, made
  by downscaling each frame) and either no weapon overlay for opponents or downscaled weapon
  pictures, since overlays are composited into the frame at its size. A 48 x 48 frame (36
  blocks) is the middle road.

**Half-size opponents, built (2026-10-31, branch `link4`).**
- The Bat in the shrink test was not visible because resource 453 is a monster sprite whose
  pictures come from the enemy picture cache, which a character never loads; its VRAM was
  still taken, so the test proved the budget but showed nothing.
- Now the four opponents draw from 32 x 32 sheets: sprite table rows 304, 306, 307 and 308
  (empty in the original) hold them, `layout.tsv` lists them, and
  `scripts/gen-opponent-sprites.py` makes `spr_304/306/307/308.png` at build time from
  `spr_300` to `spr_303` (each 2 x 2 block becomes its commonest solid colour). The pictures
  are not committed, as they derive from the game's art; `build.ps1` runs the script. The
  rows reuse the animation scripts of 300 to 303 (the tsv's last column) and carry twice the
  scale, 0x180 for 0xc0. In `placement.c`, a character on the enemy side of a link battle
  takes the half-size sheet and no weapon layer (`ArenaLink_OpponentSprite`).
- **The ROM grows by 20 KB.** The sprite data region is packed to its fixed end, 0x08320000.
  `main.ld` now starts the last region at 0x08325000 and the image is padded to 0x08805000
  (`ROM_END_tbs=` on the make line, set in `build.ps1`). A GBA cartridge can be up to
  32 MB, so nothing else cares.
- **Result:** the block table at target selection is entries 0 to 3 at 64, 4 to 7 at 16, the
  UI entries, and **162 blocks free** (was over budget by 30). All four of ours and all four
  of theirs are drawn, with no flicker, through the full linked battle to the result
  screen (`link_full`).
- **The cost: opponents look about two thirds the size of the party.** A sprite is drawn
  at most twice its frame size (a double-size affine box, `Render_PlaceProjectedSprite`
  clamps the scale at 2.0), so a 32 x 32 frame cannot reach the party's 64 x 64 at the
  battle camera's zoom. Weapons are not drawn on opponents. Possible improvements: stand the
  opponents a little closer to the camera, or use 64 x 32 / 32 x 64 frames (32 blocks; not
  tried; the pictures sit at different x offsets, so cropping needs per-picture offsets).

**Control, to prove the offset is needed:** the same four-a-side build with only the table
put back in unit 3 shows **three** opposing characters, and the intro reads "EnemyMia
appeared! (blank) appeared!": the table overwrote the fourth unit's record, so its name is
empty and its side is not set. Moving the table to unit 4 fixes it.

**Djinn in a 4v4 link (`link_djinn_*.txt`, `link_dj4_*.txt`).** Both consoles bought a
Djinni (Flint) for Isaac at the manager and linked. In the command row, Fight gives Attack,
Psynergy, **Djinn**, Item, Defend. Isaac set Flint and used it: the other console showed
"EnemyIsaac unleashes Flint! Garet takes 69 damage!!!" and the casting console "Isaac
unleashes Flint! EnemyGaret takes 69 damage!!!" (both 69). The tables crossed through the
moved slot: after the turn the casting console's own table count was 1 and the other's
**opponent table, in unit 0x84, read 1 as well** (and 0 on the console that did not cast).
So the table sits and updates correctly in the fifth enemy unit.

**Djinn over several turns, and a Summon (2026-10-31, `link_recover_*.txt`).** Both consoles
bought Flint and Granite for Isaac and fought five turns in a linked 4v4. Readings of this
console's recovery table and of the opponent's (unit 0x84) at the start of each turn,
entries as element, index, unit and turns:

| Turn starts | This console's table | Opponent's table (as seen here) |
|---|---|---|
| 1 | empty | empty |
| 2 (Flint used) | Flint, standby (-1) | Flint, unit 0x80, standby |
| 3 (Granite used) | Flint, Granite, both standby | the same, unit 0x80 |
| 4 (both summoned Ramses) | Flint 1, Granite 2 turns | the same |
| 5 | Granite 1 | the same |
| after 5 | empty | empty |

- **Identical on both consoles at every turn**, with the opponent's unit translated
  (0x00 becomes 0x80). There was no desync.
- Setting a standby Djinni again ("Flint is set to Isaac! Flint is set to EnemyIsaac!")
  removes it at once; a Summon puts every Djinni it uses into recovery, counting down by one a
  turn.
- With two Djinni standing by, the command row gains a Summon icon beside Djinn; its list
  showed "Ramses" (two Djinn) and "Venus" (one). Ramses crossed the link and both sides took
  its damage.

**Different versions (2026-10-31).** Linking the four-a-side build against a three-a-side
build of the same hack (`ROM1=` in `link.c`, a second ROM for player 1; the stock game
cannot reach the lobby without a save, and shares the three-a-side protocol): with the
same signature the two lobbies accept each other, each waits for records the other does not
send, and both end with **"The link was disconnected."** after the receive timeout. No
crash or hang, but a poor message. Fix, patch 14: the four-a-side build publishes its own
signature word (`BSA4`), and while a player waits for an opponent, a partner with another
word for one second makes the attendant say **"Your opponent has a different version of the
game!"** and stop waiting. Seen on the four-a-side console; **the other console (stock or
three-a-side) says nothing**, as the stock lobby simply leaves a console with a different
word out, and cannot be changed. Two matching builds still link and fight to a result
(`link_full`).

**Not yet checked:** saving and the series interacting with a linked battle (the
"Battle results were saved." write after New Game); a real stock ROM (needs a save that
reaches the Battle Arena); more than two Djinn of one element in a Summon; party members
dying mid-turn changing the order of commands (the test scripts assume none die).

## Recommended route (revised)

**Revised after the baseline above: build 4v4 on the real-time link first; the
offline-record route is a later fallback.** The text below describes the fallback and
is kept; step 3 (4v4) is now the first thing to do.

**The offline-record route** (fallback) reuses most of this and avoids the hard part.

1. **A party record file.** Export a party as the same bytes the link sends: four
   units (0x154 each) and the recovery table (0x140): about 1.7 KB. That is a small
   save-like file or code. Where it lives (the save, a dedicated slot, a code the
   player types or copies) is a design question, not a technical one.
2. **A virtual opponent.** Run the existing linked-battle code with the opponent
   *local*: load the record into the enemy units exactly as the receive would, and
   supply the opponent's actions from the computer instead of the serial. The stock
   code has the pieces: `AutoBattle_BuildActions` (a plain attack, as a floor) and
   `BattleAI_ChooseAction` (an enemy's chosen move, but it works from an enemy
   definition, not a received unit). A usable AI for a received party needs new work;
   that is "Route B" from the roadmap, and this is where it earns its keep. The risk
   is how much AI is enough to feel like a person.
3. **4v4 in the link code** (needed for both routes): the changes listed under
   question 4, behind a switch, with the recovery table moved.
4. **Then real time**: the two-console driver is already the test bed. Linking two
   people over a network is a different project, tested in increments (local, then
   a relay).

## Next steps (not done)

- Drive the linked battle through to a result in the driver (mash A on both).
- Change a stat or Djinn on one console and confirm it on the other (question 3).
- **Test 4v4 with Djinn set and used** (set Djinn in the manager on both consoles,
  then a Djinn command, standby, a Summon, and recovery over turns), since that is
  exactly what the moved table carries.
- Turn the `link4` prototype into a patch (it is a working branch only; the durable
  record of the work is this document and the diff summary above).
- Decide the record's home (save, code, file) and the virtual opponent's AI scope.
- The Lost Age: confirm its record is the same shape (the unit struct's `enemyId` is
  "read as the unit's id" there, per the source comment), and decide on party switching.

## Caveats

- The driver's barrier is loose (two frames of slack); it is a test tool, not an
  emulator frontend. A run that deadlocks is stopped by a 240-second watchdog.
- The first successful linked battle used the stock Multiplayer flow, which our
  attendant menu goes into unchanged. The hack's other changes (the series, saving)
  were not exercised against it, and nothing here changes how they behave in a
  linked battle.
- Both consoles in the test ran the same script and the same save, so the two parties
  were identical.

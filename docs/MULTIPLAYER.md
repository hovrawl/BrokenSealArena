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

**Control, to prove the offset is needed:** the same four-a-side build with only the table
put back in unit 3 shows **three** opposing characters, and the intro reads "EnemyMia
appeared! (blank) appeared!": the table overwrote the fourth unit's record, so its name is
empty and its side is not set. Moving the table to unit 4 fixes it.

**Not yet checked:** a battle where Djinn are actually set and used (the tables in the
test were empty, so the renumbering and the Djinn menu in a 4v4 link are untested);
a 4v4 through to a result; saving and the series interacting with a linked battle;
and a stock (3v3) ROM against a hacked one (they will not link).

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

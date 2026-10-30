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
   - the battle's sprite slots and turn order for four enemies, which I did not read:
     the enemy side normally has up to six sprites (`BattleSprite_IsSmall`), and
     characters are not "small", so four may not fit beside any other sprite.
   - **both consoles must run the hack**: a hacked game's exchange will not match a
     stock one's.

## Recommended route

**Do the offline-record route first.** It reuses most of this and avoids the hard part.

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
- Prototype the 4-unit exchange with the recovery table moved, and run it in the
  driver; read the sprite-slot and turn code for four opponents first.
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

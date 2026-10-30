# Roadmap

Where the hack is going, in the order to do it. Last updated 2026-10-30. This is
a plan, not a promise: each phase ends in something you can play and check, and
the next phase is chosen after looking at it. What each patch does today is in
`docs/CHANGES.md`; why the repo is shaped as it is is in `docs/WORKFLOW.md`.

## The goal

The Broken Seal turned into a team-versus-team arena: you build a party in the
manager, fight ladders of CPU teams, keep your progress, and in the end **take
your team into a 1v1 against another player's**. Long term, the same hack on The
Lost Age, with both games' data and characters in one hack.

Two rules shape every phase:

1. **We live on top of upstream.** Our code is in our own files, upstream files get
   short hooks, and upstream moves only when we choose (`scripts\try-upstream.ps1`
   first). A change that makes that harder needs a good reason.
2. **Verified before reported.** Build, smoke-test, look at the pictures. Taste
   review in the emulator is the user's, so the headless run should have caught
   everything else.

## Decided

These came from the user and are not open:

- **A save keeps where the player got to**: which tournament and which rung, on
  top of the usual game state (stats, Djinn, items, coins).
- **A series survives a break.** Between rounds the player is never forced into
  the next fight. They can walk away to heal, shop and upgrade, then approach the
  gate again and carry on from the same rung. Only losing, finishing, or an
  explicit "give up" ends a series.
- **The first Gauntlet must not need max levels or maxed classes.** A sensibly
  built party should be able to clear it.
- **The attendant has two menus.** Not in a Gauntlet: the current menu (Solo or
  Multiplayer, then the tournament). In a Gauntlet: a new menu that asks whether
  to give up, Yes or No.
- **A loss ends the whole series.** No retry is offered; the player goes back to
  the counter.
- **Interfaces are finalised before any Gauntlet design**, and built from written,
  reusable rules (`docs/UI.md`) so we do not go back and forth on look and feel.
- **Multiplayer (1v1, team against team) is the end goal, and it is 4v4.** How to
  get there is Phase 4.

## Where we are

Done and smoke-tested: New Game into the arena (level 30 party, 1500 coins), the
attendant's Solo/Multiplayer and tournament menus (one tournament: the 12-rung
Monster Gauntlet), the party manager (stats, Djinn, Psynergy, item shops) built
from the game's own shop parts, coins per win, saving through the Pause menu and
loading with Continue. The patch series is seven layers, our code is in our own
files, and the trial run for new upstream commits works.

Known gaps against the decisions above:

- After a win the attendant asks yes or no, and **No ends the series** (the
  series flag is cleared and the win count reset). Nothing lets the player pause
  and come back.
- A save is written as if no series is running (`arena_save.c` clears
  `FLAG_MONSTER_BATTLE` for the write), so a loaded game starts a new series.
- Only rungs 1 to 3 have been played; only the four starting characters exist;
  one tournament; English only; the stock arena still talks about link cables and
  resets the party order on load.

## Phase 0: finalise the interfaces

Goal: every screen the player sees in the arena is designed, built and reviewed
before we tune a single fight. Gauntlet design then rests on screens that will
not change under it.

The rules are in `docs/UI.md`: design intents (native look, reuse first, words
are messages), a build process, hard rules from what went wrong before (font,
wrapping, clearing, icon limits), standard layouts to copy, a catalogue of the
finished screens, a review checklist and a spec template.

| Item | Size | Notes |
|---|---|---|
| Agree `docs/UI.md` | S | Review the intents and rules; fix anything that does not match how you want the game to feel. This is the document that saves back-and-forth. |
| Spec the remaining interfaces | S | One filled-in spec (UI.md section 7) for each row of UI.md section 8: give up (Yes/No), after a win, after a loss, tournament choice, progress display. Review the specs, not code. Drafted in `docs/UI-SPECS.md` (S1 to S6, with six questions at the end). |
| Build them | M | Mostly reuse: the stock yes/no, the attendant speaking a message, the icon row. New messages go at the end of `en.po`. |
| Smoke-sheet every state | S | A script per interface that reaches every state, with a stock screen in the sheet to compare against. |
| Review in the emulator | S | Your pass, on pictures that have already been through the checklist. |

Decided for this phase (`docs/UI-SPECS.md`): Start stays as it is; progress is
told in speech ("Round 4 of 12"); giving up is not a loss and keeps the best
streak; rung 12 cleared is a win and ends the series; the heal after each win
stays; after a loss the party is restored to full and the standard spawn is used.

Exit: the catalogue in `docs/UI.md` covers every arena screen, each reviewed.

## Phase 1: a series you can leave and come back to

Goal: start the Gauntlet, win a few fights, go and shop, save, quit, load, walk
back to the gate, and carry on from the same rung. Losing, finishing or giving up
ends it. Its screens are the Phase 0 ones; this phase is the logic behind them.

**Status (2026-10-30).** Phase 0 is done (S1 to S3 built and reviewed, patch 8).
Phase 1 so far:
- Done: PR #1 landed; **pause and resume** (patch 8); **series state in the save**
  (patch 9): the round and the series flag survive a save and Continue, tested
  with `resume.txt`; **every rung loads** (`rungs.txt`: all twelve teams, within
  six sprite slots).
- Done (patch 10): **the tournament flag** (`FLAG_ARENA_TOURNAMENT`, persistent byte
  0x7f8, found by scanning every flag range for computed uses) and a **second
  tournament, the Boss Rush** (six rounds, a different ladder) with **healing
  switched off** (`ARENA_HEALS`): the win and the manager's exit do not heal, tested
  with HP carried into the next fight. It also exercises a per-tournament round
  count, per-tournament messages, and saving and resuming a non-default tournament.
- Left: playing every rung and the balance pass (now data only: the Boss Rush's
  round 1 is too hard to win by pressing A, the Gauntlet is unplayed past round 1),
  and the stock text and party order. The table below keeps the original
  descriptions.

| Item | Size | Notes |
|---|---|---|
| Land PR #1 (the layered series) | S | Everything below builds on it. |
| Pause and resume | M | Change the post-win flow in `BattleArena_RunRoundResult` and the attendant: after a win, report the coins and leave the series running (no forced yes/no, no auto-start); `BattleArena_EnterBattle` (the gate, step trigger 10) already starts a monster battle at once while the series flag is set, so stepping back into the circle resumes it. While a series runs the attendant shows the give-up Yes/No instead of the Solo/Multiplayer menu. A loss ends the series and returns the player to the counter, with no retry. The manager and its free heal are available in between. Smoke script: win, walk to the manager, buy, return, fight again. |
| Series state in the save | M | Store `{tournament, rung}` where it survives a save, and stop `ArenaSave_Begin` clearing the series (it now hides it so a load does not replay a reward). Unknown to settle first: which of the series flags and `linkTallies` the stock save already keeps (the best-streak tally is saved by `BattleArena_SaveMonsterBattleResults`, which suggests tallies have their own path), and that a load must not replay `BATTLE_ARENA_AFTER_MONSTER_WIN`'s reward. Prefer a game flag byte (as `FLAG_MONSTER_BATTLE_WINS` is) for the rung and one for the tournament. Smoke: save mid-series, reload, check the rung with `peek`. |
| A tournament flag | S | The same tournament byte, read by `ArenaLadder_Select`, so more than one ladder can exist. Needed for Phase 2's second tournament, and it is the "which tournament" in the save. |
| Check every rung loads | S | Poke the rung in a smoke script and look at each rung's first frame: sprite slots within six, nobody missing, names right. Rungs 4 to 12 have never been seen. |
| Play every rung and balance | M | A smoke script per rung that fights by mashing A. Record win or loss and the turns in a table here. **Target: a sensible party clears the Gauntlet without max levels or maxed classes.** Variables: the party's level (all four start at 30), Djinn (see below), gear bought, the stat and Psynergy shops, the coins earned (200 + 100 per win). Fix the round 3 boss spike. If a rung is unfair, change the data, not the code. |
| Stock text and party order | S | Remove the link-cable lines from the attendant's talk; keep the party order across a load. |

**Djinn are a balance variable.** Setting a Djinni on a character raises their
stats and can change their class, so a party with Djinn set is stronger than the
stat shop alone suggests. The first balance pass should test it: set Djinn on the
party, see which classes that gives, and how far the Gauntlet goes with and
without. The first Gauntlet is not tuned around them yet; the table records what
they do so the later tournaments can be.

**Levels are not designed yet.** The party starts at level 30 and the ladder
targets run from 10 to 45. Whether characters level up (from fights, from the
shop) and how their growth fits the ladder is open. The balance pass should find
out where level 30 plus purchases and Djinn stands against each rung before we
design it.

Exit: pause, shop, resume and save and load all work and are scripted; every rung
seen and played; a written balance table; a sensible party clears the first
Gauntlet.

## Phase 2: more to do

Goal: a reason to return after the Gauntlet. Pick from these once Phase 1 is
played; they are independent.

| Item | Size | Notes |
|---|---|---|
| A second tournament | M | A second ladder (`gArenaLadder` is one table today) chosen from the attendant's menu, with its own theme and rewards. Needs the tournament flag. Teams are rows of `enemy_table.c`; a rung stays within six sprite slots. May assume Djinn and levelling. |
| Levels and growth | M | Design after the Phase 1 findings: how characters grow beyond buying stats. |
| Rewards beyond coins | M | Items, Djinn or Psynergy for clearing a tournament; the manager's stock changing as you progress. |
| Characters beyond the four | L | The party is fixed at Isaac, Garet, Mia and Ivan. More means more recruits in the manager and the right sprites in battle and in the shop's strip (CHILD sprites are the open question). Investigate before committing; this may be much larger than it looks. The 4v4 link battle (Phase 4) needs only the four we have. |

Exit: at least one new thing to do that has been played end to end.

## Phase 3: teams that behave like teams (a decision gate)

Today the CPU side is mixed teams of ordinary monsters with scaled levels ("Route
A"). The alternative is CPU teams built as real player-style units with their own
Djinn, Psynergy and command choices ("Route B"). It is much more work and more
risk: new command AI and new unit data in battle.

Do not start it on a hunch. After the Phase 1 balance pass, play the Gauntlet and
decide: if fights are fine, Route A stays; if they feel flat, spike Route B on one
rung first (one hand-built team that uses Djinn and a summon) and judge that.

## Phase 4: 1v1, team against team

**Spike done (2026-10-31): see `docs/MULTIPLAYER.md`.** Two copies of the hack link
in libmgba and play a real linked battle (3v3, the stock limit), so local linking is
a yes; 4v4 has one real obstacle (the opponent's Djinn table lives in the fourth
enemy unit); internet play is a separate project. Decisions from the user: 4v4, only
the story characters, offline party records first (send your record, the AI plays
it), real time later in increments. The text below is the plan as it stood before the
spike and is kept for the questions it asked.

You said you have no idea how to get there, so here is what is already true and
what is not known.

**What the stock game already does.** The Battle Arena has a linked battle: two
players, each with a Game Boy Advance and a link cable, talk to the attendant and
step into the circle, and the game exchanges their parties over the link
(`BattleArena_ExchangePartyRecords`, `SendPartyRecords`, `ReceivePartyRecords`:
about 0x154 bytes a unit) before the battle. Our attendant's Multiplayer choice
already goes into that stock branch. So the game side of 1v1 largely exists; the
work is making it run, and fit our hack. Things that follow from the code:

- **The stock exchange is three a side; ours must be four.** A linked battle takes
  the first three party members (`FLAG_LINK_BATTLE_ARRANGED`,
  `LOBBY_UNIT_RECORD_COUNT` is 3). Our party has four and the goal is 4v4, so the
  exchange has to grow to four units: a change to the link protocol (the send and
  receive loops, the record count, how the battle seats a fourth enemy). Both
  players must run the hack, and a hacked game will not link with a stock one.
- **Both players need the same build.** The records carry the units as built, so
  stats from our shop should travel with them, but ids and layouts must match.
  That means one released version for both players.
- **Our edits to the arena touch this path** (the attendant's menu, the pause
  between rounds). Phase 1 must leave the stock link flow intact.

**What is not known (a research spike, before any plan):**

1. Can two copies of the hack link at all in an emulator on one machine? mGBA has
   multiplayer windows that emulate the link cable, and libmgba exposes a lockstep
   mode for linked cores; unverified that our headless driver can run two, which
   would let a smoke script test a linked battle.
2. Can two players do it over the internet? Emulators link locally only; remote
   play needs a relay or netplay tool, and none is chosen. This is the hard part
   and the likeliest to decide the shape of the feature (how players meet, whether
   a turn-by-turn lockstep over latency is tolerable).
3. Do the exchanged records include everything our shop changes (base stats,
   Djinn, Psynergy, gear)? Read the record builder before assuming.
4. Is a second ROM build needed for testing, or can both emulators load the same?

Exit of the spike: a written answer to those four, a recommended route, and a
smoke script that links two instances if (1) is yes. Then plan the feature.

## Phase 5: something to hand to a player

Goal: someone with their own copy of the game can play the hack.

- A binary patch (BPS or xdelta) as a release artifact, built from a clean
  checkout of the pinned upstream plus our patches, applied to the player's own
  original ROM. `tbs-en` reproduces the original byte for byte, so the base is well
  defined (`docs/WORKFLOW.md`). Both players of a 1v1 need the same release.
- Player-facing instructions and a changelog. Never publish a ROM, a save or
  anything extracted from one.
- Check upstream's licence terms for what we may distribute, and credit it.
- Other editions need their own `.po` messages (today only `en.po` has them) and
  are a translation question, not a code one. Likely out of scope.

Exit: a patch file and a short README that a stranger can follow.

## Phase 6: The Lost Age

Blocked on upstream decompiling `games/tla`. The pieces to prepare now cost
nothing: the layered patches, the port notes in `CHANGES.md`, and our code in our
own files (so the port is "re-hook a handful of files"). When `games/tla` builds:

1. Run the `patch-porter` agent to port the layers one at a time, building after
   each, as the trial run already does for upstream updates.
2. Decide what "one hack" means: the two games' data live in different images
   and different tables. A spike to load one game's characters in the other's
   arena is needed before this is more than an idea.

## Later (ideas, not scheduled)

Ideas from the user that the current design leaves room for. None blocks a phase
above.

- **Stats per gauntlet type.** Possible, and cheap, but ours to build: the stock
  tallies (`gMainRoutineWork.linkTallies`: wins, losses, best streak, current
  streak) are one set for all monster battles, not per tournament. The save
  writes the whole `MainRoutineWork` struct (0xd20 bytes) and the game flags, and
  checksums them, and the struct has unnamed spare bytes ("no code names it":
  about 0x84 after the Lucky Wheel prizes and 0x50 after the halt fields, plus a
  few small gaps). A few bytes per tournament (attempts, wins, losses, clears,
  best round) fit and are saved and checksummed for free. Where to put them, in
  order of safety:
  1. **Story-only persistent flags.** The game flags are 0x200 bytes; the hack only
     reaches the arena, so most story flags are never read. We can list which flags
     the code reachable from the arena (the shops, battle, saving, the arena
     itself) refers to, and the rest are free to hold counters (the scene and area
     temp ranges are cleared on a scene change, so they are not candidates). This
     needs only the TBS source, not the Lost Age.
  2. **The struct's unnamed bytes.** "No code names it" is not proof the original
     never used it: the Lost Age may read some of it when a TBS file is
     transferred. Wait for the Lost Age decomp, then compare what its transfer
     reads before claiming any.
  We would not delete or shrink anything: the struct's size and offsets are fixed
  by asserts and by code that reads fields by offset (`units` at 0x2c0), and the
  file has room, so the gain is repurposing bytes, not saving space. Keep every
  claimed byte named in one header so a later move is a one-file change. The
  tournament flag (Phase 1) must exist first, as the key. Until then the stock
  tallies are enough and the stock record write into the file stays off.
- **Post-battle events.** Today every outcome is the attendant speaking a line
  and the standard spawn. Wanted: a minor event for each win, a major one for
  winning a whole tournament (rung 12 is a plain win for now), and a bespoke one
  for a loss. Needs a hook where `BattleArena_RunRoundResult` picks the line, so
  an event can be chosen by outcome and tournament.
- **A proper tournament win.** Rung 12 ends the series as a win with one line and
  no data. A real one shows what the run was: rewards, a summary, perhaps the
  record.
- **Fight data.** Record every action in a fight (who acted, the move, the
  target, the damage or healing, the element and type), then derive the numbers
  by replaying the log: damage by character, by move type, by element, turns.
  Logging each action is the base; the breakdowns can be simulated later from it.
  It would also feed the balance pass. **The log is not saved** (decided): it is
  kept in memory for one fight round, used for a summary or the post-battle event,
  and cleared at the next round. A round is a few dozen actions at about 8 bytes
  each, so 1 to 2 KB. Where it lives is not yet measured: the general EWRAM heap
  (`gEwramHeap`, 0x02030000 to 0x02038000) is 32 KB shared by the field, battle and
  menu work, and nobody has checked what a battle leaves free. First step: read the
  heap's free space during a battle with the headless driver's `peek`. The battle
  also has its own random seed (`gBattleRandomSeed`), so recording the seed and the
  chosen commands may be enough to replay a fight and derive the numbers offline.
- **Difficulty modifiers.** Switch off the automatic heal after a win, probably
  per tournament and maybe as a player option. Keep the heal one call a
  tournament setting can skip.
- **Djinn and levels** as balance variables are in Phase 1.

## Cross-cutting

- **Tests:** the smoke suite checks pictures. Add `peek` assertions where a value
  matters (the rung, the tournament, the coins, a stat after a purchase) so a
  regression fails without someone looking.
- **Upstream updates:** run `scripts\try-upstream.ps1` before any update; it takes
  minutes and names the commit that broke us.
- **CI:** the build needs the original ROM, which cannot be in the repo, so hosted
  CI cannot build it. The local trial run is the substitute.
- **Housekeeping:** done (2026-10-31): the merged branches are deleted here and on the
  remote, and the experiment branches in `~/alchemy` too (`arena` and `main` are
  what is left; `arena-trial` is recreated by each `try-upstream` run).

## Still open

1. **Is a four-unit link exchange feasible?** The Phase 4 spike answers it, since
   the goal is 4v4.
2. **Which Phase 2 item first?** I would take the second tournament; the
   characters item should be investigated before it is promised.

## Order, in short

PR #1, then Phase 0 (agree `docs/UI.md`, spec and build the remaining
interfaces), then Phase 1 (pause and resume first, because the save design depends
on it; then series state in the save and the tournament flag; then rungs seen and
played and the balance pass). Run the Phase 4 spike alongside, since it is
research and its answer should not wait until the end. Then the Phase 3 gate,
Phase 2 and Phase 5 in whichever order you want a playable thing first. Phase 6
waits for upstream.

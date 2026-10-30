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
| Spec the remaining interfaces | S | One filled-in spec (UI.md section 7) for each row of UI.md section 8: give up (Yes/No), after a win, after a loss, tournament choice, progress display. Review the specs, not code. |
| Build them | M | Mostly reuse: the stock yes/no, the attendant speaking a message, the icon row. New messages go at the end of `en.po`. |
| Smoke-sheet every state | S | A script per interface that reaches every state, with a stock screen in the sheet to compare against. |
| Review in the emulator | S | Your pass, on pictures that have already been through the checklist. |

Open for this phase: whether Start closes arena screens as it does the stock
menus; where progress (tournament and rung) is shown; whether giving up counts
as a loss in the tallies.

Exit: the catalogue in `docs/UI.md` covers every arena screen, each reviewed.

## Phase 1: a series you can leave and come back to

Goal: start the Gauntlet, win a few fights, go and shop, save, quit, load, walk
back to the gate, and carry on from the same rung. Losing, finishing or giving up
ends it. Its screens are the Phase 0 ones; this phase is the logic behind them.

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
| Characters beyond the four | L | The party is fixed at Isaac, Garet, Mia and Ivan. More means more recruits in the manager and the right sprites in battle and in the shop's strip (CHILD sprites are the open question). Investigate before committing; this may be much larger than it looks. Note a 1v1 link battle takes three a side (Phase 4). |

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

## Cross-cutting

- **Tests:** the smoke suite checks pictures. Add `peek` assertions where a value
  matters (the rung, the tournament, the coins, a stat after a purchase) so a
  regression fails without someone looking.
- **Upstream updates:** run `scripts\try-upstream.ps1` before any update; it takes
  minutes and names the commit that broke us.
- **CI:** the build needs the original ROM, which cannot be in the repo, so hosted
  CI cannot build it. The local trial run is the substitute.
- **Housekeeping:** delete the leftover branches in `~/alchemy` (`spike-newfile`,
  `arena-trial`); keep `arena-chrono` until PR #1 is merged and has been used for a
  while.

## Still open

1. **Does giving up count as a loss for the tallies?** (Phase 0.)
2. **Does Start close arena screens, as it does the stock menus?** Ours do not
   handle it today. (Phase 0.)
3. **Where is progress shown?** Tournament and rung, for example in the
   attendant's speech or the manager's prompt. (Phase 0.)
4. **Is a four-unit link exchange feasible?** The Phase 4 spike answers it, since
   the goal is 4v4.
5. **Which Phase 2 item first?** I would take the second tournament; the
   characters item should be investigated before it is promised.

## Order, in short

PR #1, then Phase 0 (agree `docs/UI.md`, spec and build the remaining
interfaces), then Phase 1 (pause and resume first, because the save design depends
on it; then series state in the save and the tournament flag; then rungs seen and
played and the balance pass). Run the Phase 4 spike alongside, since it is
research and its answer should not wait until the end. Then the Phase 3 gate,
Phase 2 and Phase 5 in whichever order you want a playable thing first. Phase 6
waits for upstream.

# Roadmap

Where the hack is going, in the order to do it. Last updated 2026-10-30. This is
a plan, not a promise: each phase ends in something you can play and check, and
the next phase is chosen after looking at it. What each patch does today is in
`docs/CHANGES.md`; why the repo is shaped as it is is in `docs/WORKFLOW.md`.

## The goal

The Broken Seal turned into a team-versus-team arena: you build a party in the
manager, fight ladders of CPU teams, and keep your progress. Long term, the same
hack on The Lost Age, with both games' data and characters in one hack.

Two rules shape every phase:

1. **We live on top of upstream.** Our code is in our own files, upstream files get
   short hooks, and upstream moves only when we choose (`scripts\try-upstream.ps1`
   first). A change that makes that harder needs a good reason.
2. **Verified before reported.** Build, smoke-test, look at the pictures. Taste
   review in the emulator is the user's, so the headless run should have caught
   everything else.

## Where we are

Done and smoke-tested: New Game into the arena (level 30 party, 1500 coins), the
attendant's Solo/Multiplayer and tournament menus (one tournament: the 12-rung
Monster Gauntlet), the party manager (stats, Djinn, Psynergy, item shops) built
from the game's own shop parts, coins per win, saving through the Pause menu and
loading with Continue. The patch series is seven layers, our code is in our own
files, and the trial run for new upstream commits works.

Known gaps: only rungs 1 to 3 have been played; a loaded game starts a new
series; only the four starting characters exist; one tournament; English only;
the stock arena still talks about link cables and resets the party order on load.

## Phase 1: a loop that is fun to repeat

Goal: start, fight the whole Gauntlet, lose or win, come back tomorrow, and it
feels fair.

| Item | Size | Notes |
|---|---|---|
| Land PR #1 (the layered series) | S | Everything below builds on it. |
| Check every rung loads | S | Poke the series' win count (`linkTallies[3]`) in a smoke script and look at each rung's first frame: sprite slots within six, nobody missing, names right. Rungs 4 to 12 have never been seen. |
| Play every rung | M | A smoke script per rung that fights by mashing A, with the party's level and gear as a variable. Record win or loss and the turns it took in a table here. This is the balance pass's data. |
| Balance pass | M | Use the table: enemy levels, coin rewards (200 + 100 per win) against prices (stats scale with base, Psynergy 150 + 50 per PP, Djinn 500), and the round 3 boss spike. Decide the target: "a fully upgraded party just clears rung 12". |
| Save the rung | M | Today a save is written as if no series is running, so Continue starts a new one. Decide what a save means (see Decisions). Needs a game flag byte or the existing `FLAG_MONSTER_BATTLE_WINS`; the rung must survive the save and the stock arena's resets. |
| A tournament flag | S | A game flag byte that `ArenaLadder_Select` reads, so more than one ladder can exist. This is the prerequisite for Phase 2's second tournament. |
| Stock text and party order | S | Remove the link-cable lines from the attendant's talk; keep the party order across a load. |

Exit: every rung seen and played, a written balance table, a save that keeps your
place, and a smoke run for each. If a rung turns out to be unfair, change the
data, not the code.

## Phase 2: more to do

Goal: a reason to return after the Gauntlet. Pick from these once Phase 1 is
played; they are independent.

| Item | Size | Notes |
|---|---|---|
| A second tournament | M | A second ladder (`gArenaLadder` is one table today) chosen from the attendant's menu, with its own theme and rewards. Needs the tournament flag. Teams are rows of `enemy_table.c`; a rung stays within six sprite slots. |
| Rewards beyond coins | M | Items, Djinn or Psynergy for clearing a tournament; the manager's stock changing as you progress. |
| Characters beyond the four | L | The party is fixed at Isaac, Garet, Mia and Ivan. More means more recruits in the manager and the right sprites in battle and in the shop's strip (CHILD sprites are the open question). Investigate before committing; this may be much larger than it looks. |
| Rematch and rest options | S | Healing between rounds is already free; decide if that is right once the balance pass is done. |

Exit: at least one new thing to do that has been played end to end.

## Phase 3: teams that behave like teams (a decision gate)

Today the CPU side is mixed teams of ordinary monsters with scaled levels ("Route
A"). The alternative is CPU teams built as real player-style units with their own
Djinn, Psynergy and command choices ("Route B"). It is much more work and more
risk: new command AI and new unit data in battle.

Do not start it on a hunch. After the Phase 1 balance pass, play the Gauntlet and
decide: if fights are fine, Route A stays; if they feel flat, spike Route B on one
rung first (one hand-built team that uses Djinn and a summon) and judge that.

Multiplayer (the stock link battle) is a separate question: it needs two
emulators linked, and the attendant's Multiplayer branch is the stock one. Treat
it as research (can the headless driver link two instances?) before planning.

## Phase 4: something to hand to a player

Goal: someone with their own copy of the game can play the hack.

- A binary patch (BPS or xdelta) as a release artifact, built from a clean
  checkout of the pinned upstream plus our patches, applied to the player's own
  original ROM. `tbs-en` reproduces the original byte for byte, so the base is well
  defined (`docs/WORKFLOW.md`).
- Player-facing instructions and a changelog. Never publish a ROM, a save or
  anything extracted from one.
- Check upstream's licence terms for what we may distribute, and credit it.
- Other editions need their own `.po` messages (today only `en.po` has them) and
  are a translation question, not a code one. Likely out of scope.

Exit: a patch file and a short README that a stranger can follow.

## Phase 5: The Lost Age

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
  matters (the rung, the coins, a stat after a purchase) so a regression fails
  without someone looking.
- **Upstream updates:** run `scripts\try-upstream.ps1` on a schedule or before any
  update; it takes minutes and names the commit that broke us.
- **CI:** the build needs the original ROM, which cannot be in the repo, so hosted
  CI cannot build it. The local trial run is the substitute.
- **Housekeeping:** delete the leftover branches in `~/alchemy` (`spike-newfile`,
  `arena-trial`); keep `arena-chrono` until PR #1 is merged and has been used for a
  while.

## Decisions needed from you

1. **What does a save mean?** Options: (a) save between series, as now, and the
   Gauntlet restarts (simple; the rung is lost); (b) save keeps the current rung
   and resumes it (needs care so a load does not replay a reward); (c) both: save
   at a rung boundary only. I would take (b) with a one-rung checkpoint.
2. **How hard should the Gauntlet be?** "A fully upgraded party just clears rung
   12" is my proposal for the balance target; say if you want it harder.
3. **Which Phase 2 item first?** I would take the second tournament; the
   characters item should be investigated before it is promised.
4. **Is Multiplayer in scope at all?** It changes how much of the stock arena we
   keep.

## Order, in short

PR #1, then Phase 1 top to bottom (rungs seen, rungs played, balance, rung save,
tournament flag), then the gate in Phase 3, then Phase 2 and 4 in whichever order
you want a playable thing first. Phase 5 waits for upstream.

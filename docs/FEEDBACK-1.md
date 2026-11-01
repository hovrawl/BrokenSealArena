# Owner feedback, round 1 (2026-11-02): the plan

The list the owner wrote after playing the cups, with the answers to the open questions. Each
item is an agent task, run one at a time. Status is kept in `CHANGES.md`.

| # | Item | Decided | Status |
|---|---|---|---|
| 1 | After a first clear, the cup's trophy does not show until the save is reloaded | a bug: refresh the lobby after the clear scene | queued as "arena polish" (1) |
| 2 | Each cup has its own trophy design | nine distinct sprites, not tier groups | polish (2) |
| 3 | The save file list shows the trophies per cup, L and R turn the pages | store a bitmask of cleared cups | polish (3) |
| 4 | The scout and champion stand too close to the gate NPC | move them | polish (4) |
| 5 | Warn when the next round is a boss or mini-boss | a marker per round in `cupdata.py`, one extra message page | polish (5) |
| 6 | Stat boosts by round wins | see below | done: patch 0043 (CHANGES 43) |
| 7 | An NPC in the back shows each character's classes (class viewer) | see below | done: patch 0044 (CHANGES 44), branch `class-viewer` |
| 8 | An NPC that explains general mechanics | one NPC with a topic menu | done: patch 0045 (CHANGES 45), branch `mechanics-npc` |

## Stat boosts by round wins (replaces the coin stat shop)

- The story's stat-boost items found in chests are **not given as usable items**. Winning the
  round that holds one adds to "the number of times a boost of that stat can be applied"
  (the item's fixed amount, for the stat the item is for).
- **One party-wide pool**: a boost spent on Isaac cannot be spent on Garet.
- It **replaces the coin stat shop** in the same place with the same screens: the coin and
  price display becomes "available" and "used" counts (tweakable later). **Reset and
  reallocate** are allowed. The total is capped by the boosts the cups give.

## Class viewer NPC

An NPC at the back of the lobby. Steps: **select a character**; **see a class line** (L and R
change the line); **highlighting a class shows its Djinn breakdown and stats**; **selecting a
class shows its Psynergy**. A **"Now" / "All" toggle** (the Select button changes the filter):
now = the classes the character's Djinn can reach at present; all = every class of the line.

## Mechanics NPC

One NPC for now, with a topic menu: weaknesses, element power, the damage calculation, the
chance to unleash, the chance of status effects, and how to tell a physical attack from a
magical one and which stat affects which, defence included (docs/RELOADED-DESIGN.md has the
rules).

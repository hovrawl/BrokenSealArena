# Progression by cups (owner's direction, 2026-11-01)

## Decided

- The game is a **battle simulator**, not a story replay: Reloaded's changes are good enough
  to use without the story, for people who have played it many times. Players do not start
  from level 1.
- **Cups are linear.** A cup is a tournament for a level bracket (tens: 10s, 20s, ... up to
  99). The sequence **mimics story progression**: a cup simulates a story region (mobs picked
  from that area's encounters, capped by the area's boss). **A cup sets the party's level.**
  Finishing a cup **unlocks the next level gate**, more Djinn and more items. The first cup
  can start the party as low as level 10.
- **Side cups** sit beside the main line: themed or scenario cups for fun, or cups that
  challenge a mechanic (for example needing poison or other debuffs). **The Boss Rush is one
  kind of side cup**, not at the super-boss tier; a super-boss tier may include one.
- **Stat boosts (the stat shop) are an end-game tool for level 99 only**, to tune for the
  super-boss tier.
- **4v4 PvP has two brackets, a cap of 50 and a cap of 99, and players may play either.** 50
  is the standard cap, for builds without heavy optimisation; 99 is for players who tune
  builds hard. (A linked battle sets both parties to the chosen bracket's level, or checks
  that they match; to design.)

## Still open (the owner is thinking)

- What the 50-to-99 brackets contain (the design intent from 50 to 99).
- How the unlock state is stored (persistent flags below 0x7f8 are free) and shown (the
  attendant's menu lists cups, locked ones greyed).
- The Luck cap in the stat shop (Reloaded: luck 40 is immunity to stun, sleep and more).
- Whether a bracket-50 PvP party is built from the cups' unlocks (Djinn, items) or from a
  fixed loadout.

## Fits with

Psynergy learnt by class and level (each bracket opens its tier); Reloaded's enemy tuning per
area; the existing tournaments (Monster Gauntlet, Boss Rush) and their ladder tables
(`arena_ladder.c`, each rung a team and a level, with `ARENA_ROUNDS` per tournament); the
lobby signature (patch 14) which should also carry the PvP bracket.

## Plan (agents run one at a time; each branch is reviewed and merged before the next starts)

1. **Data port** (running): Reloaded's tables into our source.
2. **Cup framework spec**: read the formation and enemy tables for the story areas (is an
   area recorded per formation?), list candidate mobs and bosses per bracket, and write the
   spec (data format for a cup, level setting, unlock flags, attendant menu, rewards).
3. **Cup framework build**: linear cups in `arena_ladder.c` terms: a cup table, the party
   level set at cup start, unlock flags in the save, the attendant menu and a smoke test
   across two cups; the Boss Rush becomes the first side cup.
4. **PvP brackets**: the lobby asks for 50 or 99, both parties are set to it, the signature
   carries it, a linked test at each.
5. **Balance pass** over the cups with Reloaded's rules (data-only changes).

## Revision, 2026-11-01 (supersedes the items above where they differ)

- **Cups are data** (rounds, teams, rewards, requirements). They do not set the party or its
  level.
- **The level is a gate.** New Game starts the party at level 10 with only the first cup
  open. **The first win of a main cup plays an event scene** that congratulates the player
  and announces the unlocks: the next level (the party is raised to it), Djinn to buy,
  shops, cups. Older cups can be replayed while over-levelled.
- **10 to 50** is the base progression (the story's mobs stop at level 43). **50 to 99** is
  open-ended: an endless run with randomly picked, scaled mobs; Crossbone Isle is the model
  for a post-game challenge. Medium term.
- **The Psynergy shop is retired.** The **stat shop stays** for now (not level-99-only); Luck
  and status ailments will be explored separately.
- **4v4 PvP** keeps the 50 and 99 brackets.

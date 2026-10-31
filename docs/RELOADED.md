# Golden Sun Reloaded: what it changes, and a plan to replicate it

Reference notes on the community rebalance "Golden Sun Reloaded" (forum topic 2779, see
`PROGRESSION.md`), written 2026-11-01 after reading its patches, changelog and Excel
documentation. It is somebody else's work: **its files are kept in `reloaded/`, which is
git-ignored and never committed**, and the aim here is to understand and re-implement
its ideas as our own patches (in source), crediting it and asking its authors before we
reproduce their numbers wholesale.

## Decision (2026-11-01)

**Build their logic into our own changes, whole, rather than patching theirs on top.**
The owner will tell the authors about the project; either route was acceptable, but the
long-run plan is one source tree whose changelist contains the rebalance. Reasons: we
already change the engine; an IPS cannot be applied to our layout anyway; their patch is
at a stable version (v1.83a, only enemy balance expected to move), so this is a good
moment to take it whole; and ports to The Lost Age (its own patch, v1.83) follow the same
way.

How, in short: the engine changes are written by hand in C (our own files, one switch each);
the data changes are **generated once** from the patch (`ips-table-diff.py` shows every
changed field; a converter rewrites our source tables) and then committed as ordinary
source patches, so nothing depends on the IPS afterwards. A throwaway "apply theirs to
ours" step is not needed. The side-by-side test against a patched stock ROM (plan point 2
below) is **optional**: the owner is not keen on it; smoke battles with our own checks are
enough.

The patch series would grow by layers in the order from the plan review: rules, ailments,
abilities with classes, items, then enemies, Djinn and characters, and the text each needs.
Generated reports of their numbers are written to `build/reloaded/` (ignored), not
committed.

## What is in the folder

| File | What it is |
|---|---|
| `GSTBS Reloaded v1.83a.ips`, `GSTLA Reloaded v1.83.ips` | the patches, **IPS format** (not a custom binary): a list of byte ranges to overwrite |
| `TBS Full Changelog.txt`, `TLA Full Changelog.txt` | version history, v0.1 to v1.83 |
| `Psynergy Documentation.xlsx` | per-element spell tables (level, area, PP, power), buffs, elemental physical attacks (EPAs), healing maths |
| `Class Documentation.xlsx` | class multipliers, vulnerabilities, who can reach each class, growth tables, level 99 stats |
| `Class Setup.xlsx` | 13,830 rows: the class each character gets for each Djinn combination |
| `Items, Equipment, & Unleash Documentation.xlsx` | weapons, unleashes, armour, accessories, shop stock for both games, TLA drop rates, credits |

The workbooks cover both games (Felix, Piers and Sheba appear throughout); the Broken
Seal patch is a subset of the Lost Age one.

## Reading the patch

An IPS file is records of (offset, bytes), offset 0 being the first byte of the ROM, so
it can be read without hex-editing. Three small tools in `scripts/` do it (standard
library or binutils only; none reads the owner's cartridge dump):

- `ips-regions.py PATCH ELF`: which symbol each changed range falls in, by bytes.
- `ips-code-diff.py PATCH ROM ELF FUNCTION...`: the Thumb assembly of a function before
  and after. It needs a **build of the unmodified game**, so the symbols line up: made
  from source in a second worktree, `~/alchemy-stock` (upstream's pinned commit; it
  builds without any ROM). The patched copy lives only in memory.
- `xlsx-overview.py BOOK [ROWS | --sheet NAME]`: the workbooks, read as plain text.

**The TBS patch changes 1,705 ranges, 50,302 bytes:**

| Area | Bytes | Records | What |
|---|---|---|---|
| Text (messages, names, descriptions) | about 18,600 | 90 | new names and descriptions, which carry the numbers |
| `gClass_DefinitionTable` | 5,971 | 232 | class multipliers, element requirements, taught Psynergy and levels |
| `gEnemy_Definitions` | 3,799 | 443 | enemy stats, Psynergy sets, weaknesses |
| `gAbilityDefinitions` | 880 | 369 | spell power, PP cost, effects |
| `gItem_DefinitionTable` | 711 | 303 | weapon, armour and accessory stats |
| `gEnemy_ElementPresetTable` | 669 | 29 | enemy element levels |
| `gCharacter_DefinitionTable` | 344 | 11 | starting stats and growth |
| `gDjinn_DefinitionTable` | 137 | 28 | Djinn stat bonuses |
| **Code** (about 1,000 bytes in about 15 functions) | | | see below |
| Graphics and layout (icons, menu panels, a few data blocks) | a few thousand | few | "Menu Panels Revamped", icons |

So most of it is **data in tables we already have in source** (the same tables the
Psynergy report reads), and a small amount is genuine engine change.

## The engine changes (code), as far as read

Verified by disassembling the changed functions against the stock build:

- **Level-up is deterministic** (`Unit_LevelUp`, six places). Stock adds a random 0 to 19
  to each stat's growth and divides by 20 (stochastic rounding). Reloaded computes the
  gain from the level and the growth difference with no random roll (the changelog:
  "Level up doesn't depend on RNG").
- **Ailment success** (`Battle_RollEffectSuccess`). Stock: base rate plus three times the
  caster's element-level lead over the target, less half the target's luck, plus 25 for
  a weakness. Reloaded replaces the element-level term with **the target's level divided
  by 4**, and **adds a byte read from the unit record at offset 0x46** (the new
  "Ailment" attribute: equipment can raise it, the item panel shows it); the final
  comparison also changes from `>=` to `>`.
- **Base rates per effect** (`Battle_GetEffectBaseSuccessRate`): the stock switch is
  rewritten (changelog: death 25 to 20, damage plus death 10 to 5, HP to 1 35 to 30;
  recovery from debuffs lowered).
- Also changed, not yet decoded: `BattleAbility_ApplyToTarget` (about 330 bytes: the base
  damage formula gains MaxPP / 8, healing, "may ignore 50% of defense" with a luck check,
  EPA multipliers), `Unit_Calculate` (stat caps, the Power/Res cap bug, regeneration),
  `Ability_ApplyToTargets`, `gAbilityBattleEffects` (effect table), and the Djinn menu
  preview, stat-boost and command collection routines (UI and Djinn debuff changes).

## The changelog by theme (TBS)

- **Damage and healing maths:** base damage formula changed (MaxPP / 8 added to base
  power); PP cost of every base damage and healing spell recalculated by a formula;
  healing power and its elemental multiplier changed; summon HP% fixed; power and
  resistance cap bug.
- **Ailments and effects:** an Ailment item attribute; debuff chances raised and recovery
  chances lowered, then adjusted; two-stage debuffs weaker; death and "HP to 1" rates
  cut; Djinn debuffs more likely; the 50%-defense-ignore effect needs a luck check.
- **Spells:** powers and PP costs (Avalanche, Magma Storm, Nettle, Stone Spire and
  more), learning levels (the last Psynergy is learnt at level 42), per-spell tweaks.
- **Classes:** multipliers and Psynergy sets reworked repeatedly (see the class doc).
- **Items:** a full rebalance of accessories; weapons, unleashes (multipliers on every
  EPA and attack unleash), healing item strength and prices, accessory effects.
- **Enemies:** agility, defense, HP, Psynergy sets, weaknesses; "every non-overworld
  Djinn can't escape"; bosses retuned (Killer Ape, Manticore, Hydros Statue, Kraken,
  Deadbeard).
- **Stats:** PP gain (10 more from level 19 to 39), growth after 39 reduced, level 60 to
  99 growth lowered.
- **Interface:** Menu Panels Revamped, an item stat-boost randomness removal patch.

## Things that are easy to miss

1. **It changes the engine, not just numbers.** About 15 functions. Most of the "mechanical
   changes" you listed need real C, and each also has a history of bugs in the changelog
   (Power/Res cap, ailment success, Mud, Deadbeard regeneration, Healing ePower, Flash).
   Each fix is a test case for us.
2. **A spare byte becomes a stat.** The Ailment attribute is read from offset 0x46 of the
   unit record, which is `unused[0]` in the decompilation ("no code names it"), so the
   record does not grow. It still touches the item table, `Unit_Calculate` (which sums
   it from equipment), the status and item screens, and means the byte now travels
   meaningfully in **the link exchange** (the whole unit record is sent). (Checked: the
   same code reads the target's level at 0x0f and luck at 0x42, matching `struct Unit`.)
3. **They are the same numbers we would be changing.** Their enemy rows are the rows our
   ladders use (`arena_ladder.c`), so any enemy retune moves every rung's difficulty.
   Their class vulnerabilities (the "Vulnerabilities" column) also decide **what can
   ail a player in 4v4**, which is balance we have not thought about.
4. **The class tables are our progression design.** `Class Setup` is exactly the "Djinn
   set decide the class" mapping, and their Psynergy levels (1 to 42) matter because all
   our characters start at level 50, so every pool is open from the start.
5. **Linked battles need identical rules.** Both consoles run the same battle code; if
   damage or ailment rules differ between builds the two will desync. The lobby signature
   (patch 14) must change whenever the rules or tables do.
6. **Text carries the numbers.** 18 KB of their change is message text (descriptions that
   state powers and effects); changing a number without its description leaves the game
   lying. Our `en.po` is the only edition that builds, which makes this easier.
7. **Their numbers are for a story game.** Shops, drops (TLA), early game curve, boss
   spikes: not our arena, so much of it is context, not a spec.
8. **Credit and permission.** The workbooks carry a credits sheet. We should credit them,
   and ask before copying values rather than re-deriving our own.
9. **The patch can't be applied to our build.** Our layout differs from the original ROM
   (we compile from source, and patch 13 moved a region), so an IPS would corrupt it.
   Replication has to be source changes.

## Plan review

Your order (mechanics, then enemy ailment susceptibility, then skill, item and class
tunings) is sound and mostly dependency order: the PP cost formula and spell powers only
make sense once the damage formula is fixed. Suggested changes:

1. **Build the differ first (a small tool step).** Extend the three scripts into a table
   differ: for the ability, class, item, enemy, element-preset, character and Djinn tables,
   apply the IPS to the stock build in memory and print **a field-level diff** (for example
   `Avalanche: power 110 to 105`). It is exact (no transcription errors from reading
   spreadsheets) and the workbooks become the cross-check, not the source. It also gives
   the complete list of code changes to decode.
2. **Use the patched stock ROM as an oracle.** The stock build with the IPS applied
   (made from source, in scratch) plays the reference. Run the same scripted battle in it
   and in ours and compare damage and ailment results. That turns "replicate" into a
   checkable test for each mechanical change, in the smoke driver we already have.
3. **Switch each mechanical change separately** (for example `ARENA_RULES_LEVELUP`,
   `_AILMENT`, `_DAMAGE`, `_HEAL`), in our own file (`arena_rules.c`) with short hooks, so
   each can be turned off, tested and ported to the Lost Age on its own. That follows the
   existing convention (one switch per layer).
4. **Make ailments the second step, as you say, but split it:** (a) the formula and the
   Ailment attribute (engine), (b) per-enemy susceptibility (data: enemy `weakEffects`,
   the base rates, element presets). Stock bosses fail the roll for ordinary reasons (the
   target-level and luck terms, three weakness slots at plus 25), so we should confirm
   from the data which of these actually makes bosses immune before copying a fix.
5. **Do classes and skills together, not as separate steps.** Psynergy learning levels
   live in the class table (`abilities`), the requirements and multipliers are in the same
   rows, and our new "Psynergy by class" design (PROGRESSION.md) is about those rows. Spell
   power and PP (the ability table) stay a separate pass, as they depend only on the
   damage formula. Items last, since they depend on the Ailment attribute and the
   unleash multipliers.
6. **Keep the arena's own constraints in the loop.** Start level 50; coins and the stat
   and Djinn shops; the ladders; 4v4 symmetric play. Reloaded's numbers assume a levelling
   curve we do not have, so the balance pass in the roadmap becomes "their rules, our
   progression".
7. **Tie the version to the lobby signature** (patch 14) from the start, so mismatched
   rules cannot link.
8. **Decide what not to take.** Interface patches (Menu Panels Revamped) overlap our own
   interface rules (`UI.md`); the story-only tuning (shops, drops, early bosses) has no
   place here.

Open decisions for you: whether to ask the authors first; whether we copy their numbers
or use them as a starting point we then rebalance for the arena; and whether the Ailment
attribute (a struct field, and a link and save format change) is worth it, or whether
class vulnerabilities and the base rates alone give enough control.

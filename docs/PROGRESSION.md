# Progression: Psynergy, classes, Djinn and growth

Notes for Phase 2 ("Levels and growth", "Rewards beyond coins" in `ROADMAP.md`).
Nothing here is built or decided yet except where marked **Decided**. It records the
owner's intent (2026-11-01) and what the game's own data does, to design from.

## Intent (the owner's words, tidied)

- **Decided: Psynergy is not bought.** The base game already teaches it by **class**, and
  it is not permanent, which is liked: change the class and the Psynergy changes.
- The **class comes from the Djinn a character has set**: Venus-only Djinn lead down the
  Squire, Knight, Lord line and so on (other pairs make the other series).
- So **the class limits the pool**, and **each Psynergy has its own level requirement on top**.
- Growth is part of this: levels, Djinn (which also add stats) and class together are the
  progression. A balance pass waits until the logic has been tested (it is data-only).
- Consequence for what exists: the party manager's **Psynergy shop** (patches 5 and 6)
  contradicts this and is a candidate to retire or turn into something else. Not decided.

## How the data is stored (read from the decompilation, 2026-11-01)

Verified in `~/alchemy` (`games/tbs`); nothing here needs new code to read.

- **`gClass_DefinitionTable`** (`src/game/class_table.c`, 203 rows, `struct ClassDefinition`
  in `include/game/character.h`). One row per class:
  - `series`: which line of classes it belongs to (Squire and Knight are series 1; the later classes of the line follow in the table).
  - `required[4]`: the element levels it needs, in tens, one per element.
  - `hp, pp, atk, def, agi, luck`: the class's multipliers, in tenths of the base stat.
  - `abilities[16]`: pairs of `{ability, level}`. **This is the Psynergy the class
    teaches and the character level each needs.** An empty pair is a gap.
  - `weakEffects`: ability effects the class is weak to.
- **`Class_Determine`** (`src/game/game/classes.c`) picks the class: it takes the two
  strongest elements of the character's **set Djinn** (a second element below level 1 does
  not count), chooses the series from them, and then takes the **last class of that series
  whose `required` levels are all met**. Isaac and Garet as children and Jenna have fixed
  classes (200 to 202); it returns 0 for no class.
- **`Unit_UpdateClass`** reruns it whenever a Djinni is set or put on standby.
- **`Unit_RefreshPsynergy`** (`src/game/game/levels.c`) rebuilds the Psynergy list from the
  class: it drops everything the old class and the equipped items gave (tagged
  `PSYNERGY_FROM_CLASS` 0x8000 and `PSYNERGY_FROM_ITEM` 0x4000), keeps what was taught for
  good (untagged), then adds each class ability whose `level` the unit's level has reached,
  and the Psynergy of equipped items. It runs when class, level or equipment changes. This
  is the "not permanent" behaviour.
- **Djinn** (`struct DjinnDefinition`) add flat stat bonuses while set, before the class
  multiplies them, so Djinn move both class and stats (noted in `ROADMAP.md`'s balance
  section).
- Psynergy can also be **taught for good** (`Unit_LearnPsynergy`, item and quest
  effects) and **granted by an equipped item** (`ITEM_USE_TEACHES`, the eight Psynergy items).
  The arena's Psynergy shop presumably uses the first kind (not checked).

Open questions for the design:
- Do all four characters reach the classes the owner wants with the Djinn the arena can
  sell, and is there a Djinn pool big enough? (The manager sells Djinn today; check the
  stock against the class `required` columns.)
- Should some Psynergy still be permanent (the "taught for good" kind) or none?
- What does the shop do instead, if it goes? (Rewards for clearing a tournament are the
  roadmap's other Phase 2 item.)

## Reference material (for later review, not adopted)

The Lost Age hacking community's mod page for a difficulty and rebalance hack:
<http://forum.goldensunhacking.net/index.php?topic=2779.0>. It is **not a binary or game
code hack**; it is data changes, so it is a source of ideas and breakdowns only, and
its patch, if reviewed later, may show what they changed. It links these spreadsheets
(Google Sheets, one per area), which break down the data this document talks about:

- Class: <https://docs.google.com/spreadsheets/d/1W9VJcbmV5l6wGSiDO4oM6IV566i7XvVFQs_5WT0ajN8>
- Class setup: <https://docs.google.com/spreadsheets/d/1prjK1L0YpeKuadoy5A2liiAWm_m0yZ3oOc-FE5rGQKU>
- Equipment: <https://docs.google.com/spreadsheets/d/13eCQOiM5YsKmcBZKSlwW4-wExXtn8WZ4U46cL_hmRO8>
- Psynergy: <https://docs.google.com/spreadsheets/d/1qVYsowdD3n_g3kjvdGl8UBryidcRU1rJaEebiDaPrlA>
- RNG guide (drops, GameFAQs):
  <https://gamefaqs.gamespot.com/gba/561356-golden-sun-the-lost-age/faqs/25734>

Caveats: the page is about The Lost Age, and their numbers are tuned to their difficulty
and rebalance, so nothing is taken as is. None of it has been opened or checked here;
this is a bookmark. The version at the time of saving was 1.83 (updated 2026-05-16).

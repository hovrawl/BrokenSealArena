# Cup framework: specification

Status: **implemented in patch 0027 (see CHANGES.md entry 27); the text below is the spec as written.** Not done: counter-style cup list, trophies, cups D to G gear beyond a few items (`cup-gear.py --missing`), balance pass. Written 2026-11-01 for the builder agent (plan step 3 in
`CUPS.md`). Source read: `~/alchemy` branch `arena` (`games/tbs`). Every claim carries a file and
line; every guess is marked **GUESS** and every gap **UNKNOWN**. Numbers come from the generated
`cup-candidates.md` (run `scripts/cup-candidates.py`; it reads our enemy table, so levels are the
Reloaded retune). Paths below are relative to `games/tbs` unless they start with `docs/` or `scripts/`.

Contents: 1 Areas, 2 Brackets and cups, 3 Level setting, 4 Data format, 5 Unlock state and saves,
6 Menus, 7 Balance hooks and risks, 8 Implementation plan, 9 Decisions for the owner, 10 Unknowns.

## Revision by the owner, 2026-11-01 (read this first; it supersedes the text below where they differ)

The spec below was written with cups that **set** the party and its level. The owner's
answer is different, and simpler:

- **A cup is data**: rounds, teams, rewards and what it requires. **It does not set or
  control the party or its level.** (So `ArenaCup` has no party level, and `KEEP_LEVEL`
  and the "per bracket or per cup" question D1 go away.)
- **Level is a gate the player earns.** The party starts at level 10 (New Game). Only the
  first cup is open at first. **Beating a main cup for the first time plays an event
  scene** that congratulates the player and tells what it unlocks: **the next level (the
  party is raised to it), Djinn to buy, shops and cups.** The party's level therefore
  only ever goes up, so section 3's `ArenaCup_SetLevel` reduces to "raise to level N"
  (`Unit_LevelUpTo`), at the unlock event and at New Game; lowering is not needed, and the
  risk that setting a level wipes stat-shop boosts disappears.
- **Older cups can be replayed while over-levelled**, if the player wants.
- **10 to 50 is the base progression** and should cover the story mobs, which (section 0)
  stop at level 43, so this holds. **50 to 99 is not designed and can stay open-ended**: an
  endless run that picks and scales mobs at random is the idea; **Crossbone Isle** (the
  story's super-dungeon) is a good model for a post-game challenge; medium term.
- **The Psynergy shop is retired** (D4: yes). After the Reloaded changes no Psynergy is
  limited to the shop.
- **The stat shop stays as it is for now** (not level-99-only). Luck, and how statuses
  and immunities work around it, is to be explored separately before it is touched (D6
  deferred, D7 onwards open).

Answers to the rest (owner, 2026-11-01):

- **D3, Gauntlet and Boss Rush:** both are just examples of cups. **The Monster Gauntlet is
  retired** (it was basic). **The Boss Rush becomes one of the first extra (side) cups,
  unlocked after the base progression is finished.**
- **D5, resets:** **none.** Starting a cup does not change the party in any way: no gear
  or Djinn reset, no level change.
- **D7, money:** the **start purse stays 1500 coins** (enough for a Djinni and some items).
  **The first-clear bonus is gear**, tied to the cup's region (the research in this spec
  says what the region offers).
- **D8, names:** by place, as in 2.2 (Vault Cup, Kolima Cup, Mercury Cup ...). **Each boss
  can be a cup; later cups group several bosses** so there are not too many.
- **D9, regions with no scripted boss:** the check below found why: **the story has no
  boss fight in those places.** In Goma Cave, Suhalla Gate, Altmiller Cave and Babi
  Lighthouse the only scripted battle is a **Djinn battle** (`Field_RequestDjinnBattle`:
  Forge, Dew, Squall and Luff); Kolima Forest, Bilibin, Fuchin and the lower Venus
  Lighthouse have random mobs only. So the guessed caps in 1.3 are replaced by a better
  rule: **cap such a cup with its region's Djinn battle** (the Djinn enemies are rows #150
  to #163) or with the strongest mob trio, and let the later bosses (Tret, Saturos, Killer
  Ape, Hydros, Kraken, Toadonpa, the Lizards, Menardi and Saturos, Fusion Dragon) cap the
  cups they already own. The builder should check the Djinn-battle scenes first.

### Proposed: five main cups (the owner's idea, 2026-11-01; for the owner to confirm)

The story's scripted bosses are nine (levels from `cup-candidates.md`): Tret L14; Saturos
(Mercury Lighthouse) L18; Killer Ape L18; Hydros Statue L20; Manticore L22; Kraken L25;
Toadonpa L27; Storm and Tempest Lizard L28; Saturos and Menardi L38 with the Fusion Dragon L39.
The caped strangers (Mystery Man and Woman, L10, four sprite slots) are too strong an opener
by their stats, and **Deadbeard (L43, Crossbone Isle) is kept for the post-game**. Grouping the
bosses by level gives **five main cups**, one per bracket, with the party's level before each
one being 10, 20, 30, 40 and 50 (the first four first clears raise it; the fifth opens the
extras):

| Cup | Party level | Regions (mobs) | Bosses |
|---|---|---|---|
| 1 | 10 | Sol Sanctum and Vale, Goma Cave, Kolima Forest, Tret Tree | Tret (L14) |
| 2 | 20 | Bilibin, Mercury Lighthouse, Fuchin Falls, Mogall Forest | Saturos (L18), Killer Ape (L18) |
| 3 | 30 | Altin Peak, Lamakan Desert, Vault, Altmiller Cave | Hydros Statue (L20), Manticore (L22) |
| 4 | 40 | Tolbi, Colosso, Gondowan and Lunpa, Suhalla | Kraken (L25), Toadonpa (L27), Storm and Tempest Lizard (L28); the Colosso trio (L25) is a candidate round |
| 5 | 50 | Suhalla Gate, Babi, Venus Lighthouse | Saturos and Menardi (L38), then the Fusion Dragon (L39): the last dungeon |

After cup 5: the Boss Rush and the other side cups, then Crossbone Isle (Deadbeard) as the
first post-game challenge. This leaves the unlocks per cup (Djinn, shops, gear) to be
spread over five steps (section 2.2's eleven-cup table folds into it: its Djinn and shop
columns add up the same, grouped five ways). **Open:** the cup 4 load (four bosses, check
the round count), the strangers as a side cup, and the gear rewards per cup.

### Revised proposal: seven main cups (owner's change of mind, 2026-11-01; supersedes the five above)

Changes: **Saturos and Killer Ape are separate single-boss cups; the overloaded level 40 cup
is split in two; the party level need not always rise** (a cup's reward is Djinn and shop
stock, not necessarily a level); **cup levels follow the enemy levels** (a 5-level award is
allowed, some cups award less or nothing). **Shops come from Reloaded's own shop list**: its
TBS sheets name the shops (Vale, Vault, Bilibin, Imil, Kolima, Xian; the later towns Altin,
Tolbi, Kalay, Lunpa, Stucco, Suhalla and Lalivero come from our stock table, section 2.2),
so a cup simply names which shops it opens. The Djinn and shop columns below regroup 2.2's
eleven cups (its rows 1 to 4 become A, 3 is B, 4 is C, 5 and 6 are D, 7 and part of 8 are E,
the rest of 8 and 9 are F, 10 is G). Levels are a first draft to tune.

| Cup | Name (cand.) | Mobs from | Boss (enemy level) | Played at party level | First clear raises to | Djinn | Shops opened |
|---|---|---|---|---|---|---|---|
| A | Tret Cup | Sol Sanctum and Vale, Goma, Kolima, Tret Tree | Tret (L14) | 10 | 15 | Flint, Forge, Granite, Breeze | Vale, Vault |
| B | Mercury Cup | Bilibin, Mercury Lighthouse | Saturos (L18) | 15 | 18 | Gust, Fizz, Sleet | Bilibin |
| C | Mogall Cup | Fuchin Falls, Mogall Forest | Killer Ape (L18) | 18 | 20 | Fever, Zephyr, Quartz | Imil |
| D | Altin Cup | Altin Peak, Lamakan Desert, Vale Cave, Vault Cave | Hydros Statue (L20), Manticore (L22) | 20 | 25 | Spritz, Smog, Sap, Kite | Kolima, Xian, Altin |
| E | Tolbi Cup | Tolbi ship, Altmiller, Colosso | Kraken (L25) and the Colosso trio (L25) | 25 | 27 | Ember, Squall, Mist | Kalay |
| F | Lunpa Cup | Gondowan, Lunpa Fortress, Suhalla Desert and Gate | Toadonpa (L27), Storm and Tempest Lizard (L28) | 27 | 35 | Scorch, Ground, Torch, Tonic, Flash, Dew, Luff | Lunpa, Stucco, Suhalla |
| G | Lighthouse Cup | Babi, Venus Lighthouse | Saturos and Menardi (L38), then the Fusion Dragon (L39) | 35 | 50 (the base progression ends) | Vine, Corona, Hail | (none left; Suhalla stock if not given in F) |

Notes: all 28 Djinn are given once (the three of Vine, Corona and Hail and the one of Bane
after Crossbone Isle included). **After G:** the Boss Rush and the other side cups open, and
**Crossbone Isle (Deadbeard, L43) is the first post-game challenge**, giving Bane and the
Lalivero stock. G is the hardest step (the party jumps from 35 to the L38 to L39 fights); a
level 35 to 38 range for G is the thing to test. The Mystery Man and Woman (L10, four sprite
slots) stay out of the line (possible side cup). Cup F carries seven Djinn, which is a lot at
once: the first clear could also be split into two rewards if it feels heavy.

**Accepted by the owner (2026-11-01): the seven cups, with their level disparity** (Djinn give a
lot of power, so level against enemy level is a balancing act, not a rule). **Cup F's seven Djinn
at once is fine**: the player may not be able to afford them all.

**Gear comes from the dungeons, not the shops.** Shops sell what Reloaded's shop list says;
gear that the story finds in **chests** is the reward, and two mechanisms deliver it:

1. **Mid-cup first-time rewards.** A cup's data lists reward rounds: on the first time a round
   is reached, an item (or Djinni) from that region's chests is given **during the run**, so
   the player can equip it before the next fight (a Mercury Lighthouse chest item is given
   part-way through the Mercury Cup). Needs: a reward entry in a round (item id, a once-only
   flag), the item given with `PartyInventory_GiveItem` (the call the scenes use) and a message
   saying so; checking that the inventory has room (15 slots a unit; the party stock).
2. **Side cups for the rest.** Gear that is off the main path (optional chests, the rooms
   the story only passes by) is earned in side cups, themed on a dungeon: the chest contents
   of that dungeon are the first-clear rewards.

Research for the builder: list each scene's chests and their items. Chests are
`TreasureSpot` actors (`include/field/field_work.h:24`) in the scene tables, 34 scenes mention
them; write `scripts/cup-gear.py` to join scene, chest id and item (as `cup-candidates.py` does
for encounters) and assign each to a cup round or a side cup. Items that come from story events
(`PartyInventory_GiveItem` calls in scene code, for example a boss's reward) go to the cup that
holds that boss.

**Where the levels come from (checked 2026-11-01).** The enemy levels in the cup table are the
levels in our enemy table, and **Reloaded barely changes them**: only 13 of 165 enemy rows have
a different level byte, each by one to three levels (for example Manticore 20 to 22, Hydros
Statue 19 to 20, Cerberus 35 to 33). What Reloaded changes is the enemies' **stats** at those
levels (the bosses gain roughly 40 percent HP, more Attack and PP, and higher Luck: Tret HP 710
to 1012, Kraken 2400 to 3420, Fusion Dragon 5000 to 7125), so a boss of a given level is a
harder fight than in the stock game. The *party* levels in the table (10, 15, 18 ...) are our
own proposal anchored to those enemy levels, not Reloaded's; they are tuned in the balance pass.

**Djinn in cups.** The story has about two dozen Djinn battles (scenes that call
`Field_RequestDjinnBattle`, listed in `cup-candidates.md` "Djinn battles and Djinn in scenes").
Rule: **a cup may include its region's Djinn fight as a round** (one or two, not a flood), and
**a cup can end by giving a Djinni**, so that **not all Djinn need to be bought**: each Djinni is
earned in a fight, given as an end reward, or sold at the party manager once its cup is cleared.
The Djinn column in the table above is then read as "available from this cup" and the builder
splits it three ways with the scene list; the manager's Djinn stock is gated by the same state.

Still open: what 50 to 99 contains (later) and the levels above (to tune in the balance pass).

## 0. Summary

- **Area data exists, but not on the formations.** `struct Formation` has no area field
  (`include/battle/formations.h:18-27`). The area lives in the *encounter zones*
  (`src/field/encounter_zones.c`, 104 rows, commented by place), reached by scene from
  `src/field/encounter_rules.s` and by world-map region from
  `src/field/world_map_encounter_rules.c`. Bosses are the `Field_RequestBattleFromEncounterTable(zone, slot)`
  calls in `src/scene`. `scripts/cup-candidates.py` joins these (about 700 lines, a few seconds) and
  groups the zones into 20 story regions. The only hand-made part is the grouping list `REGIONS`.
- **Enemy levels run 1 to 43**, not to 50 (`cup-candidates.md`, last rows: Deadbeard L43, Fusion
  Dragon L39, Saturos and Menardi L38). Random-battle mobs stop at L28. Past 43 there is no content,
  only margin-scaling.
- **50 to 99** needs a decision (section 2.3). Recommended: bracket 50 is the TBS roster at full
  margin ("Champions"), 60 to 90 are optional hard re-runs, 99 is the super-boss tier (the only
  tier with the stat shop open).
- **Setting a level** is cheap and safe by *resetting the base stats and level to 0 and calling the
  existing `Unit_LevelUpTo`* (section 3). It uses no random numbers under `ARENA_RULES_LEVELUP`.
  The closed form is only an optimisation.
- **Unlock state** is two persistent bytes (`0x7f0` progress, `0x7e8` side-cup bits); everything
  else (Djinn on sale, shop stock, which cups are open) is *derived* from the progress byte, so
  nothing is granted twice and saves from before cups still load.

## 1. Areas: where the game records them

### 1.1 What the tables hold

| Question | Answer | Evidence |
|---|---|---|
| Does a formation know its area? | **No.** A formation is `{layout, memberIds[5], minimumCounts[5], maximumCounts[5]}`, rows of `gFormations` (380 rows). | `include/battle/formations.h:18-27`, `:30` |
| Does an enemy row know its area? | No. Rows hold level, stats, rewards. | `src/game/enemy_table.c` (165 rows used) |
| What does record the area? | **Encounter zones**: `{rate, level, enemies[ENCOUNTER_GROUP_COUNT] (formation ids), weights[]}`. The zone's own `level` is the party level it was made for. The place is in a comment above each row. | `include/field/encounter_zone.h:15-23`, `src/field/encounter_zones.c:8` |
| Which scene uses which zone? | `gScene_EncounterRules`: `{scene, entrance (-1 any), flag, shift, first zone}`; ground 0 has none, grounds 1 to 7 take consecutive zones from the rule's first. | `src/field/encounter_rules.s:1-25`, `src/field/field_sequence/encounter.c:7-9,38-49` |
| And the world map? | `gWorldMap_EncounterRules`: `{encounter region, battle environment, flag, zone}`, regions 1 to 6 and 21, 31, "made for party levels 3 to 22". | `src/field/world_map_encounter_rules.c:4-12`, `encounter.c:22-24,98-104` |
| How is a random battle picked in the stock game? | Step counter per zone, then a weighted draw from the zone's formations (`Encounter_CountStepsAndSelectFormation`). | `encounter.c:124-138`; row access `:259-265` |
| How are the story's bosses started? | `Field_RequestBattleFromEncounterTable(zone, slot)` in the scene's event code; the slot picks `gEncounterZones[zone].enemies[slot]`. Scripted-only zones: 12 (Vale and Vault), 36 (Tret and Mercury), 53 (Mogall, Altin, Lamakan), 62 (Tolbi ship), 63 and 84 (Crossbone), 72 (Colosso), 98 (Suhalla, Venus aerie). | `cup-candidates.md` "Scripted battles"; `encounter.c:259-265` |
| Djinn battles? | `Field_RequestDjinnBattle(actor, DJINNI_X)` into zones 100 to 103, one Djinni enemy row per Djinni (levels 5 to 25). | `cup-candidates.md` "Djinn battles" |
| Is the story's *monster battle* mode level-matched? | Yes in stock: `BattleFormation_SelectLevelMatchedCandidate` chooses any formation whose average level is within 3 of the party's, ignoring areas. Our `ARENA_LADDER` replaces it. | `src/battle/battle/formation.c:100-110, 492-502` |

### 1.2 How much work, and the method

Done already by the script, from source, with no hand typing of enemy ids:

1. parse `enemy_table.c` (name from the row comment), `formations.c`, `encounter_zones.c`,
   `encounter_rules.s`, `world_map_encounter_rules.c`, `character_table.c`, `djinn_table.c`;
2. group zones into regions with `REGIONS` (the only editorial list, 20 entries, ordered by the
   zones' party level, which follows the story closely but not exactly: Vale Cave and Vault are
   early in the story but their zones are level 15 to 16);
3. for each region print random formations with weights and slot counts, the scripted battles of
   its scenes, and the mobs by enemy level.

Remaining work for a builder: none for data extraction. A new upstream or a changed enemy table
only needs a re-run. **Risk:** a region's *boss* is not in the zone table, only in scene code;
the script finds `Field_RequestBattleFromEncounterTable` calls by regex, so a boss started some
other way would be missed. The Djinn battle list uses the same regex idea. Regions 2 (Goma),
3 (Kolima), 5 (Bilibin), 7 (Fuchin), 10 (Vale Cave and Vault), 13 (Altmiller), 17 to 19 have **no
scripted boss in the table** (UNKNOWN whether the story fights are scripted some other way,
for example `Event_StartBattle` with a literal formation; `grep` for it before settling bosses).

### 1.3 The regions, in story order (generated; enemy level = our table)

Mob levels are the enemies' own. "Cap" is the proposed boss; it is editorial where marked.

| # | Region | Random mob levels | Scripted bosses and mid-bosses (enemy row, level) | Cap (proposed) |
|---|---|---|---|---|
| 1 | Sol Sanctum and Vale | 1 to 4 (Vermin, Bat, Wild Mushroom, Slime, Amaze, Zombie) | Mystery Man #114 and Mystery Woman #117, L10, 4 slots; Zombie #109 L4 (Djinn tutorial) | Mystery pair |
| 2 | Goma Cave | 3 to 5 (Ghost, Skeleton, Will Head, Zombie) | none found | **GUESS** a Skeleton/Will Head/Ghost trio |
| 3 | Kolima Forest | 3 to 7 (Rat, Rat Soldier, Drone Bee, Troll) | none found | **GUESS** Troll L7 trio |
| 4 | Tret Tree | 6 to 8 (Spider, Gnome, Creeper) | Tret #139 L14 | **Tret** |
| 5 | Bilibin Cave and snowfield | 6 to 9 (Ooze, Ghoul, Grizzly) | none found | **GUESS** Grizzly + Ghoul |
| 6 | Mercury Lighthouse | 8 to 10 (Cuttle, Harpy, Siren, Lizard Man) | Lizard Man #119 L10; Saturos #115 L18 | **Saturos** |
| 7 | Fuchin Falls Cave | 5 to 12 (Mole, Dirge, Spirit, Bone Fighter) | none found | **GUESS** Bone Fighter trio |
| 8 | Mogall Forest | 11 to 12 | Ape #69 L14; Killer Ape #70 L18 | **Killer Ape** |
| 9 | Altin Peak and Lamakan | 11 to 14 (Salamander, Orc, Ape, Tarantula) | Living Statue #122 L17 x3; Hydros Statue #123 L20; Ant Lion #130 L15; Manticore #81 L22 | **Hydros**, then Manticore |
| 10 | Vale Cave and Vault | 14 to 16 (Gargoyle, Cave Troll, Brown Bear) | Bandit #21 L7 + 2 Thief #22 L6 (Vault, story-early) | **GUESS** Gargoyle + Cave Troll, or the Bandit trio as flavour |
| 11 | Tolbi ship | scripted only: L17 | Man o' War, Lizard Fighter, Virago L17; Kraken #113 L25 | **Kraken** |
| 12 | Crossbone Isle | scripted only: guards L17 to 33 | first guards L23, last guards L28 to 33; Deadbeard #141 L43 | **Deadbeard** |
| 13 | Altmiller Cave | 17 to 18 (Wight, Golem, Cerberus, Gargoyle) | none found | **GUESS** Cerberus + Golem |
| 14 | Colosso | scripted only | Azart #124/#125, Satrage #126/#127, Navampa #128/#129, all L25 | the champion trio |
| 15 | Gondowan and Lunpa Fortress | 20 to 21 | Brigand #23 L22 (x1 to x3); Toadonpa #133 L27 | **Toadonpa** |
| 16 | Suhalla Desert | 20 to 22 | Tornado Lizard #136 L25, Storm Lizard #137 L28, Tempest Lizard #138 L28 | **Storm and Tempest Lizard** |
| 17 | Suhalla Gate and Gateway Cave | 23 to 24 | none found | **GUESS** Earth Golem + Goblin |
| 18 | Venus Lighthouse, ground | 23 to 25 | none found | (merged into 20) |
| 19 | Babi Lighthouse and Tunnel Ruins | 24 to 26 | none found | (merged into 20) |
| 20 | Venus Lighthouse upper and aerie | 25 to 28 (Recluse, Boulder Beast, Thunder Lizard, Grand Golem, Fenrir) | Saturos #116 and Menardi #118, L38, 4 slots; Fusion Dragon #140 L39 | **Menardi + Saturos, then Fusion Dragon** |

Full per-region tables (formations with weights and slot counts) are in `cup-candidates.md`. Mid-region
facts a builder needs: mobs scaled up by the engine keep roughly native strength (Vermin L1 moved
to L10 has Atk 135 against a native L10 Cuttle's 110, `cup-candidates.md` "Early cups").

## 2. Brackets and cups

### 2.1 How a cup maps to the engine

A rung is `{targetLevel, formation}` (`ArenaTeam`, `src/battle/battle/arena_ladder.c:14-17`); the
enemies are moved from their mean own level to `targetLevel` by `BattleEnemy_AdjustLevel`
(`formation.c:200-216`, +9.7 HP, +12.3 Atk, +3.3 Def, +5.1 Agi a level, floor 70 percent of base, caps
9999 and 999). So a cup needs **two separate numbers**: the *party level* the cup sets, and each
rung's *target level*. The rung target may be below or above the party level (the Gauntlet today
fights rungs 10 to 45 against a level-50 party). A region's mobs therefore fit any cup level; what
decides strength is the target. Rule of thumb for data: rung targets from `cupLevel - 3` ramping to
`cupLevel + 2`, boss round at `cupLevel + 4` (**GUESS**, to be tuned in the balance pass).

### 2.2 Proposed main line (levels 10 to 50)

Brackets of ten; two or three region cups share each bracket's party level. Clearing the last cup of
a bracket opens the next bracket (the "level gate"). Djinn use the shop numbering `element * 7 + n`
(`arena_shop.c:441-443`); item tiers are shop towns from the stock table (`cup-candidates.md`
"Shop stock rows"). Djinn follow the scene each is found in (the "Every scene file" table).
All 28 Djinn are covered once.

| Cup | Name (candidate) | Regions | Party level | Rounds (**GUESS**) | Boss round | Djinn unlocked | Items unlocked (shop towns, rows) |
|---|---|---|---|---|---|---|---|
| 1 | Vale Cup | 1, 2 | 10 | 8 | Mystery Man and Woman | Flint, Forge (start with one each of Venus and Mars) | Vale 1 to 3 |
| 2 | Kolima Cup | 3, 4 | 10 | 8 | Tret | Granite, Breeze | Vault 4 to 6 |
| 3 | Mercury Cup (gate to 20) | 5, 6 | 10 | 10 | Saturos | Gust, Fizz, Sleet | Bilibin 7 to 9 |
| 4 | Fuchin Cup | 7, 8 | 20 | 8 | Killer Ape | Fever, Zephyr, Quartz | Imil 10 to 12 |
| 5 | Desert Cup | 9 | 20 | 10 | Hydros Statue, then Manticore | Spritz, Smog | Kolima 13 to 15, Xian 16 to 18 |
| 6 | Vault Cup (gate to 30) | 10 | 20 | 8 | Gargoyle pair (**GUESS**) | Sap, Kite | Altin 19 to 21 |
| 7 | Tolbi Cup | 11, 13 | 30 | 8 | Kraken | Ember, Squall | Kalay 22 to 24 |
| 8 | Colosso Cup | 14, 15 | 30 | 10 | Toadonpa | Mist, Scorch, Ground, Torch | Lunpa items 25, Stucco 26 to 28 |
| 9 | Suhalla Cup (gate to 40) | 16, 17 | 30 | 10 | Storm and Tempest Lizard | Tonic, Flash, Dew, Luff | Lunpa gear 29 and 30 |
| 10 | Lighthouse Cup | 18 to 20 | 40 | 12 | Menardi and Saturos, then Fusion Dragon | Vine, Corona, Hail | Suhalla 31 |
| 11 | Crossbone Cup (gate to 50) | 12 | 40 | 8 | Deadbeard | Bane | Lalivero 32 to 34 |

The Djinn column adds up to 28 (2+2+3+3+2+2+2+4+4+3+1 = 28 with the starters in cup 1). The order of
the *Djinn* inside a bracket is editorial. The Crossbone Isle region (12) is placed last because
Deadbeard (L43) is the highest-level enemy; the story has it earlier. Its guards run L17 to L33.

Brackets 10 and 20 hold levels where real enemies (L1 to 18) are far from the cup level; see 7.2.

### 2.3 Levels 50 to 99: honest options

TBS has nothing above L43 (`cup-candidates.md` "The enemy table by level": last rows). Engine facts
that bound what is possible, from the "Scaling check":

- Enemy Atk reaches the 999 cap near party level 80 for a normal L26 to L28 mob, so from 80 up a
  scaled enemy only gets *tankier*, not deadlier. HP keeps scaling to 9999.
- The ratio of enemy to party base stats stays nearly constant from 20 to 99 (Atk about 3.1 to 3.8,
  HP 1.5 to 3 for mobs, 4 to 22 for bosses): margin-scaling keeps the shape of a fight.
- The high-HP rows are the only credible "super" fights: Deadbeard 8550, Fusion Dragon 7125, Toadonpa
  3990, Storm and Tempest Lizard 4133 and 4275, Kraken 3420, Lizard King 2850, two Mimics (#148 L26,
  #149 L30) with 1421 and 1719.

| Option | What | Cost | Risk |
|---|---|---|---|
| A. Hard re-runs | the same 11 cups at party 50, 60, 70, 80, 90 with rung targets equal to the party level | data only (copy a cup, change levels) | repetition; Atk caps at 80 |
| B. Champions' Cup (bracket 50) | mixed teams of the top mobs (L23 to L33) plus every boss, 12 rounds, targets 50 to 58 | data only | none big; this is the Gauntlet moved up |
| C. Super-boss tier at 99 | cups built from the high-HP rows only, two bosses a round (six sprite slots), stat shop open | data only | a boss is already L43 at best; at 99 it gets about +56 levels, ratio of enemy HP to party about 11 (Deadbeard) |
| D. Boss Rush at 99 | the existing Boss Rush ladder with targets 90 to 99 | data only | already a side cup |
| E. New bosses | fill the empty enemy rows (#110 to #112 are all zero; #92 Wise Gryphon, #101 Raging Rock, #132 Doodle Bug, #135 are level-0 placeholders) | needs a sprite, abilities and AI per row | **UNKNOWN**: sprite and AI fields for those rows (not read) |

**Recommendation:** B for bracket 50 (the standard PvP cap and the end of the story-like line), A for
60 to 80 as **optional** cups (can be cut if the owner prefers), C plus D for the 99 tier. Mark
50 to 99 content as "a fixed, small number of cups" until the owner decides (section 9, D2).

### 2.4 Side cups (beside the line)

| Side cup | Idea | Mechanic it tests | Needs |
|---|---|---|---|
| Monster Gauntlet | exists (12 rungs, mixed teams, heals) | general | conversion only |
| Boss Rush | exists (6 rungs, no healing) | attrition | conversion only |
| Poison and Debuffs | teams with high Luck and tough HP that only die to Poison, Taint and stat debuffs (use the `ARENA_EFFECT_POISON` and Taint handlers, `arena_config.h:117-124`) | status play | teams with Luck under 40 (`arena_rules.c:37-57`) |
| Djinn Hunt | Djinn enemies only (rows #150 to #163, levels 5 to 25) | Djinn and summons | slot check: all large, 3 a team |
| Colosso Champions | Azart, Satrage, Navampa teams | speed and defence | exists in Gauntlet rung 6 |
| Dragon Day | Lizards and Dragons (Lizard King, Tornado/Storm/Tempest Lizard, Earth Lizard, Fusion Dragon) | resistances | data only |
| Undead Night | Ghosts, Skeletons, Zombies, Liches | Healing and Holy-type play | **UNKNOWN**: element data of those rows |

Side-cup unlock rule: `requires` = main-line cups cleared (section 4).

## 3. Level setting: `ArenaCup_SetLevel(level)`

### 3.1 Why `Unit_LevelUpTo` is not enough

`Unit_LevelUpTo` only loops while `currentLevel < targetLevel` (`src/game/game/levels.c:445-455`). Each
`Unit_LevelUp` adds to the *current* base stats (`unit->baseHp += gains->hp` ...,
`levels.c:407-412`), so lowering needs the base stats rebuilt from zero.

### 3.2 The rule being matched (closed form)

Under `ARENA_RULES_LEVELUP`, level L's gain in a stat with growth points `g[0..5]` (every 20 levels):
`band = min(L / 20, 4)`, `d = g[band+1] - g[band]`, `span = L >= 20 ? 20 : 19`,
`gain = L*d/span - (L-1)*d/span` (C integer division, truncating). Level 1 also adds `g[0]`.
Base at level N = `g[0] + sum over L = 1..N of gain(L)` (`src/game/game/arena_rules.c:18-23`,
`levels.c:372-405`). `scripts/cup-candidates.py` (`party_base`) and `scripts/levelup-check.py` implement it.
No `Random16()` is used with the rule on (`levels.c:331-335`), so a reset leaves the battle RNG alone.
Base stats at the cup levels are in `cup-candidates.md` "Party base stats by level" (for example Isaac:
L10 HP 123 Atk 50 Luck 5; L99 HP 812 Atk 338 Luck 23).

### 3.3 Design (recommended: reset, then the existing routine)

```c
/// Sets every party member to `level` (1 to 99), lower or higher than now.
void ArenaCup_SetLevel(s32 level) {
  s16 ids[8]; s32 n, i;
  n = Party_ListMembers(ids);
  for (i = 0; i < n; i++) {
    struct Unit *u = Unit_Get(ids[i]);
    s32 bonus[6];
    /* 1. bonus = base - formula(level); keep only when level == 99 (see 3.5) */
    u->level = 0; u->experience = 0;
    u->baseHp = u->basePp = u->baseAttack = u->baseDefense = u->baseAgility = u->baseLuck = 0;
    Unit_LevelUpTo(ids[i], level);           /* repeats Unit_LevelUp: base, Psynergy, Calculate */
    /* 2. add the kept bonus back */
    Unit_UpdateClass(ids[i]);                /* class from the set Djinn */
    Unit_RefreshPsynergy(ids[i]);            /* class Psynergy for the new level */
    Unit_Calculate(ids[i]);
    u->hpGauge = u->ppGauge = UNIT_GAUGE_FULL;
  }
  Party_RestoreHpPp(1);                      /* full HP and PP, cure ailments */
}
```

- **Cost.** `Unit_LevelUp` allocates a small EWRAM block, adds six gains and calls
  `Unit_RefreshPsynergy` and `Unit_Calculate` every level (`levels.c:352, 419-420`). 4 characters x 99
  levels is under 400 calls. `ArenaBoot_NewGame` already does 4 x 50 levels at boot
  (`src/scene/arena_boot.c:81-88`) with no visible stall, so the cost is proven acceptable. A
  closed-form version (sum the telescoping band terms, write six fields, call `Unit_Calculate` once)
  would be about 30 lines and is **not needed**; the reset-and-raise version cannot drift from the
  level-up rule.
- **What else resets.** Experience (set to 0, then `Unit_LevelUp` raises it to
  `gCharacter_LevelExpTable[id*99 + level - 1]` when short, `levels.c:314-326, 367-369`). Level (a `u8`,
  `battle_unit.h:276`). Base action count, regen (`levels.c:416-418` sets 1, 0, 0 per level-up).
  Stats after equipment and Djinn: `Unit_Calculate` (every level-up calls it).
- **Class and Psynergy.** Psynergy comes from the class and the level: `Unit_RefreshPsynergy` drops
  everything tagged `PSYNERGY_FROM_CLASS` or `_ITEM`, then re-adds each class ability whose level is
  reached (`levels.c:62-174`). Lowering the level therefore *removes* high abilities, as wanted.
  Permanent (untagged) Psynergy is kept: the arena's Psynergy shop makes such entries
  (`arena_shop.c:509`, `Unit_LearnPsynergyFar`), so a level-10 party that bought Psynergy at 99
  would keep it. See 3.5.
- **Djinn.** Held and set Djinn live in `djinnHeld` and `djinnSet` bit masks (`battle_unit.h:324-329`)
  and are independent of level. A cup may not need to reset them; if a bracket "kit" is wanted,
  the reset is: clear `djinnSet`, then `Djinn_Set` the bracket's Djinn (`djinn.c:127`), which re-runs
  `Unit_UpdateClass`. **UNKNOWN**: whether clearing `djinnHeld` and `djinnSet` directly leaves the
  Djinn recovery list (`DjinnRecoveryTable`, `djinn.c:99-114`) consistent; use `Djinn_PutOnStandby`.
- **Equipment.** Not level-gated in the stock game (**UNKNOWN**: confirm no equip level check). A kit
  reset is a policy choice (section 9, D5), not a technical need.
- **Exp and coins in a cup.** In a monster series enemies drop **no** experience or coins:
  `spoils.c:143-144` returns before adding them when `FLAG_MONSTER_BATTLE` is set (the arena pays a
  flat `200 + 100 * (win - 1)` itself, `battle_arena.c:1696`). So no level-up can push a party past the
  cup's level during a cup.

### 3.4 Where it runs

At series start, `battle_arena.c:1196-1203` (`answer == YES` for Solo), after a confirm prompt
(section 6). `ArenaSeries_*` runs in the same overlay; `Unit_LevelUpTo`, `Party_ListMembers`,
`Unit_UpdateClass`, `Unit_RefreshPsynergy` and `Party_RestoreHpPp` must be reachable by far call from
the overlay (`src/gamepak/far_call/GAME.S:28-34`, `src/system/overlay/imports.inc:189-190` show the
pattern: one `export`/`import` line and a `...Far` wrapper each). **Check which are already
exported** before adding any: `Unit_LevelUpToFar` is (used by `battle/debug.c:85`), `Party_RestoreHpPp`
is (used in `arena_menu.c:114`). Cheapest placement: put `ArenaCup_SetLevel` in the main image
(`src/game/game/`, a `// Part of game.c` file next to `arena_rules.c`) and export one veneer.

### 3.5 Pitfalls

1. **Stat purchases and stat items are in the base stats** (`arena_shop.c:386-407`,
   `ARENA_RULES_ITEMS`). A reset wipes them. With the stat shop at level 99 only, the natural rule is:
   compute `bonus = base - formula(level)` first; **keep it only when the new level is 99**, drop it
   otherwise (documented in the confirm prompt). Without it, a cup 99 to 99 replay would erase the
   player's boosts. Needs `formula(level)` once (the closed form), so the closed form is useful after all
   for this one purpose (**GUESS**: 20 lines).
2. **Permanent Psynergy** (arena shop, `arena_shop.c:509`) bypasses level gating, so it breaks
   "each bracket opens its tier" (`PROGRESSION.md`). Recommend retiring the Psynergy shop with this
   change (decision D4).
3. **Order of the three refresh calls.** `Unit_UpdateClass` already calls the Psynergy refresh
   (comment, `levels.c:66-68`), but call it explicitly after the level is final. Do `Unit_Calculate`
   last, then the gauges.
4. **`Unit_LevelUp` at level 99 is a no-op** (`levels.c:364`); `SetLevel(99)` after a reset reaches
   99 in exactly 99 calls.
5. **Do not call it during a battle or while the party is in the middle of a series that was
   saved at a different cup.** The cup id byte (section 5) and the level are saved together, so
   Continue is consistent; only set at series start.
6. **Memory:** `Unit_LevelUp` allocates and frees `LevelUpWork` per call (`levels.c:352, 422`); no leak.
7. **A level-1 character** (`gains->level == 1`) adds `g[0]` once. A reset to 0 means level 1 is
   reproduced exactly, including that.
8. **The linked 4v4 brackets** (cap 50 and cap 99): the lobby signature (patch 14) must carry the
   bracket so both sides call `ArenaCup_SetLevel(50|99)` or the link refuses. Out of scope here.

**Verdict:** a prototype is cheap (about 25 lines plus one far-call veneer) and safe (it replays the
existing level-up on a zeroed unit). It is *not written* in this task.

## 4. Data format: the cup table

New file `src/battle/battle/arena_cups.c` (part of `battle.c`, like `arena_ladder.c`) and the
declarations in `include/module/arena.h`. `arena_ladder.c` keeps `ArenaTeam` and `ARENA_TEAM`; its two
`static const` ladders become entries of the cup table and `ArenaLadder_Select` reads the chosen cup.

```c
/// Flags of ArenaCup.flags.
#define ARENA_CUP_SIDE       0x01  /* beside the line: not counted in progress */
#define ARENA_CUP_HEALS      0x02  /* heal after each win (ARENA_HEALS today) */
#define ARENA_CUP_KEEP_LEVEL 0x04  /* do not set the party level (legacy tournaments) */
#define ARENA_CUP_STATS_OPEN 0x08  /* the stat counter is open in this cup (level 99 tier) */

/// Themes (for the menu icon and the attendant's line; no engine effect).
enum { ARENA_THEME_STORY, ARENA_THEME_MIXED, ARENA_THEME_BOSS, ARENA_THEME_STATUS,
       ARENA_THEME_DJINN, ARENA_THEME_UNDEAD, ARENA_THEME_DRAGON };

struct ArenaCup {
  u8  partyLevel;       /* ArenaCup_SetLevel at start; 0 with KEEP_LEVEL */
  u8  flags;            /* ARENA_CUP_* */
  u8  roundCount;       /* rungs used from rounds[] */
  u8  bossRound;        /* 0-based rung of the cap; usually roundCount - 1 */
  u8  requires;         /* main-line cups cleared before this one opens */
  u8  theme;            /* ARENA_THEME_* */
  u8  shopTier;         /* highest shop town unlocked by clearing it (0 = none new) */
  u8  unused;
  u16 firstClearCoins;  /* paid once, when the progress byte advances */
  u32 djinnMask;        /* Djinn unlocked by clearing it: bit = element * 7 + n (shop numbering) */
  const struct ArenaTeam *rounds;   /* roundCount entries */
};
extern const struct ArenaCup gArenaCups[ARENA_CUP_COUNT];
```

- `ArenaTeam` stays `{u8 targetLevel; struct Formation formation;}` (12 bytes,
  `arena_ladder.c:14-17`). `Formation` holds at most **five member kinds**, fixed counts when
  `minimumCounts == maximumCounts` (`formations.h:18-27`). A cup round that wants randomness may set
  `maximumCounts > minimumCounts`; the builder then spreads extras by free slots
  (`formation.c:525-569`).
- A cup is addressed by its **index in `gArenaCups`**. Ids 0 and 1 stay the Gauntlet and the Boss
  Rush, so `FLAG_ARENA_TOURNAMENT` (0x7f8) values already in saves keep meaning the same cups
  (`arena.h:21-25`, `arena_series.c:26-31`). Main-line cups follow (2 to 12); further side cups
  after. `ARENA_TOURNAMENT_COUNT` becomes `ARENA_CUP_COUNT` (a `STATIC_ASSERT` on the table length).
- `ARENA_ROUNDS(t)` and `ARENA_HEALS(t)` (`arena.h:33-39`) become `gArenaCups[t].roundCount` and
  `flags & ARENA_CUP_HEALS`. `ArenaLadder_Select` (`arena_ladder.c:78-113`) takes the rung from
  `gArenaCups[cup].rounds[min(streak, roundCount - 1)]` instead of the `?:` over two arrays
  (`:94-95`); the margin code is unchanged.
- **Messages.** The texts say the round count ("of 12", `arena_series.c:12-22`, GOTCHAS "two number
  blanks"). With 13 or more cups of different lengths, do not carry a count in the text: use "Round {n}" for
  give-up and next-round (two generic messages) and keep **one cleared message per cup** (it names the
  cup), generated into `text/en.po` from the table by a script (`scripts/gen-cup-messages.py`).
  **UNKNOWN**: how new `msgid` numbers are allocated and how `msg_ids.h` is produced; read
  `docs/WORKFLOW.md` and the end of `en.po` first. The current layout `MsgArenaGiveUpPrompt + 3*t + kind`
  (`arena_series.c:21-22`) goes away.

### 4.1 Conversion of the existing tournaments

```c
static const struct ArenaTeam gGauntletRounds[12] = { /* the 12 ARENA_TEAM lines, unchanged */ };
static const struct ArenaTeam gBossRushRounds[6]  = { /* the 6 ARENA_TEAM lines, unchanged */ };

const struct ArenaCup gArenaCups[ARENA_CUP_COUNT] = {
  /* 0 Monster Gauntlet */ {.partyLevel = 0,
      .flags = ARENA_CUP_SIDE | ARENA_CUP_HEALS | ARENA_CUP_KEEP_LEVEL,
      .roundCount = 12, .bossRound = 11, .requires = 0, .theme = ARENA_THEME_MIXED,
      .rounds = gGauntletRounds},
  /* 1 Boss Rush */        {.partyLevel = 0, .flags = ARENA_CUP_SIDE | ARENA_CUP_KEEP_LEVEL, /* no HEALS */
      .roundCount = 6, .bossRound = 5, .requires = 0 /* GUESS: 4 */, .theme = ARENA_THEME_BOSS,
      .rounds = gBossRushRounds},
  /* 2 Vale Cup ... */
};
```

`KEEP_LEVEL` keeps today's behaviour exactly (rung targets are absolute, `targetLevel` 10 to 45
against a party of any level). The Boss Rush's `requires` is a **GUESS** (open after cup 4, or leave it
at 0 as today, decision D3). Once the main cups exist, both side cups may switch to a party level (the
Gauntlet's targets 10 to 45 suit a level-30 or 40 party; the Boss Rush's 14 to 45 suit 40).

### 4.2 The six-sprite-slot limit and its check

The battle has **six enemy sprite slots**; a small enemy takes 1, every other 2
(`formation.c:510-523, 556-559`, comment `arena_ladder.c:20-23`; `BattleSprite_IsSmall`,
`battle_sprite.c:48-57`, reads `gBattleSprites[index].isSmall`). Boss and Djinn rows are all "large".
**The engine does not guard the minimums**: `freeSpriteSlots` is only decremented by
`requiredSlots * minimumCount` (`:512-523`) and may go negative; extras are then skipped but the
minimums are still listed. What an overflowing team does on screen is **UNKNOWN**; do not rely on it.
So the limit must be enforced in the data:

1. `scripts/cup-check.py` (new, run by the builder before every export; reads `arena_cups.c` and
   reuses `cup-candidates.py`'s `parse_small` and slot sum): for every rung, sum
   `minimumCount * (1 if small else 2)` and fail above 6; fail if `maximumCounts[i] <
   minimumCounts[i]`, if a member id is a level-0 placeholder row, if more than five members are
   used, if `roundCount` exceeds the array, or if `bossRound >= roundCount`. The generated candidates
   already print `[n slots]` per formation with the same rule (`cup-candidates.py:297-310`).
2. A `STATIC_ASSERT` that `sizeof(gArenaCups)/sizeof(gArenaCups[0]) == ARENA_CUP_COUNT`.
3. Optional debug build: a runtime trap in `ArenaLadder_Select` if the slot sum exceeds six.

Typical rungs under the limit: three large enemies, or one boss plus one large, or a large and
several small ones. Which rows are small is in `gBattleSprites[].isSmall`; `cup-candidates.md` marks
the large ones.

## 5. Unlock state and saves

### 5.1 Flags

Persistent flags are those below 0x200 and from 0x400 up (0x200 to 0x2ff scene temp and 0x300 to
0x3ff area temp are cleared on scene or area changes, `main_routine.c:421-427`, `flags.h:222-230`).
The flag store is 4096 bits; byte flags start at a multiple of 8 and use the same numbering
(`src/game/game/flags.c:7-12, 72-86`). Verification for 0x7f0 to 0x7f7:

- no `#define` in `include/flags.h` has a value from 0x700 to 0x7ff (a grep of the whole header
  returned nothing; the next named flag is 0x800);
- the computed ranges stop short of it: Djinn from `FLAG_DJINN_FIRST` (`flags.h:26,35`), visited
  areas 0x180 (`:221`), shop stock 0x400 plus a row (35 rows, to about 0x422, `:242`, `stock.c:323`),
  enemy defeated 0x600 plus an enemy id (`battle_internal.h:147`; ids run to 8 + 165, so to about 0x6ad);
- no code in `src` or `include` mentions a `0x7e..` or `0x7f..` flag (grep: only unrelated hex);
- `docs/GOTCHAS.md:98-105` and `module/arena.h:15-20` list only 0x7f8 as claimed.

So **0x7f0 to 0x7f7 and 0x7e0 to 0x7ef are free**; the whole band 0x700 to 0x7ff is unnamed.

| Flag | Byte | Meaning | Written when |
|---|---|---|---|
| `FLAG_ARENA_TOURNAMENT` 0x7f8 (kept) | 0xff | **the chosen cup id** of the running or last series (index of `gArenaCups`) | Solo is chosen (`arena_menu.c:100`) |
| `FLAG_ARENA_PROGRESS` 0x7f0 (new) | 0xfe | main-line cups cleared, 0 to 11 | a main cup is cleared, to `max(old, order + 1)` |
| `FLAG_ARENA_SIDE_CLEARED` 0x7e8 (new) | 0xfd | bit n = side cup n cleared | a side cup is cleared |
| 0x7e0 (reserve) | 0xfc | second side-cup byte, or grades for the trophy work | later |
| 0x7d8 and below (reserve) | | trophies: best result per cup (for the file list) | later |

Smoke access: `rush_clear.txt` pokes the tournament byte at **0x0200013F**, which is
`gGameFlagBytes + 0xff`, so the base is 0x02000040 and progress is **0x0200013E**, side bits
0x0200013D. (Inferred from that script; confirm with a `peek` of a known flag.)

Progress is a **count**, not per-cup bits, because the line is linear. Per-cup records (trophies, best
time, grade) belong to the later trophy work and need more bytes. **UNKNOWN**: how the File Screen
could read a save's flags for the file list; the flags travel with the save but the list screen was
not read.

### 5.2 What survives a Pause-menu save and a resume (patches 7 and 9)

A running series is exactly: `FLAG_MONSTER_BATTLE` (0x173, persistent), the win count
`linkTallies[LINK_TALLY_MONSTER_STREAK]` in the saved `MainRoutineWork`, and the cup id byte 0x7f8
(`CHANGES.md` entries 8 to 10). The party's level, stats and Djinn are in the saved units. So a cup
needs **no new state to resume**: the level was set at series start and is in the save; the cup id is a
persistent byte; progress is in 0x7f0. The Pause-menu save overrides the next scene and entrance to the
arena door (entry 7) and does not clear `FLAG_MONSTER_BATTLE` (entry 9). Points to test:

1. Progress is written at the clear (in `ArenaSeries_AfterWin` before `ArenaSeries_End`,
   `arena_series.c:83-98`), after the battle. The clear message runs at once, so there is no way to
   save between the last win and the progress write.
2. **Replaying a cleared cup pays no first-clear coins** (unlocks are derived from the progress byte;
   coins only when it advances).
3. **Scene temp flags are saved raw** (GOTCHAS lines 77-80): keep no cup state in 0x200 to 0x3ff.
4. `FLAG_MONSTER_BATTLE_WINS` (0x3f8, area temp) is reset at series start (`battle_arena.c:1197`);
   unchanged.
5. A save from before cups has tournament byte 0 or 1 and progress 0. It loads; the next series start
   shows the confirm prompt and sets the level (section 6).
6. New Game (`ArenaBoot_NewGame`) must zero progress and the side bits, set the start level
   (`ARENA_START_LEVEL`, `arena.h:13`, now 50) and the purse (now 1500, `arena_boot.c:62`).

### 5.3 How Djinn and items are unlocked

Today the party manager sells **all 28 Djinn at 500 coins** with no gate (`arena_shop.c:302-303`,
`ArenaShop_Buy` `:493-512`: `Djinn_GiveFar` then `Djinn_SetFar`), 32 Psynergy (`:304, 416-425`), stats
(`:306-407`), and opens Xian's stock rows 16 to 18 (`arena_menu.c:75-77, 133-137`). Gating is by
*derived stock*, never by a flag per item:

| What | Gate | Where | Change |
|---|---|---|---|
| Djinn on sale | `unlocked` = OR of `djinnMask` of main cups with index below progress, plus the starters | `arena_shop.c:466-489, 538-600` (the Djinn panel is 3 by 4, `:25-29`) | hide or mark Djinn outside `unlocked` |
| Item shops | town tier `T` = max `shopTier` of cleared cups; the manager opens the three rows of that town in `sStockTable` (weapons, armor, supplies) | `arena_menu.c:75-77, 133-137` replaces the constant `TRAINING_SHOP_FIRST_ROW` | one function `ArenaCup_ShopRow(kind)` |
| Stat counter | open only if the unit's level is 99 (or the running cup has `ARENA_CUP_STATS_OPEN`) | `arena_menu.c:143-146` | a message when closed, section 6 |
| Psynergy counter | candidate to retire (`PROGRESSION.md`: Psynergy is not bought) | `arena_menu.c:129-131` | decision D4 |
| Cups open | `cup.requires <= progress` | attendant menu | section 6 |

Items outside shops (the "Artifacts" lists in some rows) depend on `FLAG_SHOP_ARTIFACTS_STOCKED + row`
(`stock.c:312-323`); **UNKNOWN** whether the arena's `Shop_Run` initialises them (rows 16 to 18 worked).
Rows 1 to 15 and 19 to 34 are untested in the arena: smoke every row (plan step 6). The rows were
authored for the story, so a town can sell gear far stronger or weaker than the cup suggests. The tier
table in 2.2 is the first draft of the item curve; the balance pass owns it.

## 6. Menus

Rules from `UI.md`: a choice is an icon row with a prompt, at most **four icons** (section 3 "Icons":
five left the prompt window empty); a list of things to buy is a counter; yes/no is the game's;
all words are messages in `text/en.po` (the prompts end in `{end_now}` when a menu follows, `en.po`
near `MsgArenaAttendantPrompt`). `ArenaMenu_IconChoose(prompt, icons, labelBase, count)` draws the
row and labels are **consecutive messages** (`arena_icon_menu.c:17-39`). That function has **no
disabled or greyed state**, so "locked ones greyed" needs a different tool (below). New screens need a
`UI.md` section 7 spec reviewed before code (section 2 step 4 of that file).

### 6.1 Flow

```
Attendant (no series):  [Fight = Solo] [Cable = Multiplayer]            (unchanged, arena_menu.c:89-94)
  Solo -> "Which cups?"  [Battle = Next cup] [Item = Replay] [Summon = Side cups]
     Next cup   -> confirm  "<Cup name>. Your party will be set to level N. Enter?"  Yes/No
     Replay     -> cup list (counter style), main line, cups with requires <= progress
     Side cups  -> cup list, side cups with requires <= progress
  Yes -> ArenaCup_SetLevel, series starts (battle_arena.c:1196-1204)
Attendant (series running): "Round n. Do you want to give up?"  (unchanged, arena_series.c:65-78)
```

- **Next cup** is the shortcut: the first main cup not yet cleared. When all are cleared the row
  shows "Replay" and "Side cups" only.
- **The list.** At most four cups fit an icon row, and the line has 11 or more, so the list is a
  *counter*: reuse the party manager's counters (`ArenaShop_Run`, a row of icons with a price tag, page
  arrows, description window; `arena_shop.c:292-300, 538-600`) with a new kind `ARENA_SHOP_CUPS`.
  Entry icon = a boss or element icon for the cup's theme; the price tag slot shows the party level
  ("Lv 10"); the description message is the cup's blurb. Paging is the counter's own. **GUESS:** the
  counter needs only a new `kind` in `ArenaShop_Price`, `_NameMessage`, `_DescriptionMessage`, `_Owned`
  (the five switch points at `arena_shop.c:429-489`) and no new drawing code.
- **Locked cups.** Inside the counter a locked entry uses the stock "can't buy" treatment: **UNKNOWN**
  whether the counter greys sold-out or unaffordable entries; the closest existing state is "owned"
  (`ArenaShop_Owned`, `:466-489`), drawn as the item's note instead of a price. Use that: a locked cup
  reads "Clear <previous cup> first" in the price window and cannot be chosen (`ArenaShop_Buy` returns
  its message id). If a true grey is wanted it is a palette tweak on the icon sprite (**UNKNOWN**
  cost, treat as polish).
- **The confirm prompt** is a per-cup message with one number blank for the level; `Event_AskYesNoWithActorAnimation(0, 0)` as in the give-up (`arena_series.c:72`). Because a field message shows a
  repeated number twice (GOTCHAS 74-76), put no second blank in it.
- **Series flow** for a cup, using the existing machinery:
  1. *Start:* confirm, `ArenaCup_SetLevel`, `FLAG_MONSTER_BATTLE` set, streak 0 (`battle_arena.c:1196-1203`).
  2. *Win a round:* coins `200 + 100 * (win - 1)` (`:1696`) and the heal if `ARENA_CUP_HEALS`
     (`arena_menu.c:106-115`); "Round n won! Step into the circle when you are ready."
  3. *Clear:* progress advances (main cup) or the side bit is set; `firstClearCoins` paid the first
     time; message "You cleared the <Cup name>!" naming what opened ("The Kolima Cup is open!"); then
     `ArenaSeries_End` (`arena_series.c:40-61`).
  4. *Lose:* stock loss line, party restored, series ends (`CHANGES.md` entry 8); no progress change.
  5. *Give up:* ends, not a loss (`arena_series.c:65-78`). The level stays at the cup's level.
  6. *Resume:* Continue after a Pause-menu save; the attendant asks "Round n. Do you want to give up?"
     (entry 9); cup id and level are in the save.
- **Locked-at-99 stat counter.** The manager's Characters icon opens the status strip then the
  stat counter (`arena_menu.c:143-146`). Below level 99 show the status strip only and a message on
  trying the counter: `MsgArenaStatsLocked`.
- **Messages to add** (names are proposals; wording in the game's voice, lines of at most ~20 chars,
  `{end_now}` on prompts that lead to a menu):

| Message | Text |
|---|---|
| `MsgArenaCupPrompt` | "Which cups would\nyou like?{end_now}" |
| `MsgArenaCupNext`, `...Replay`, `...Side` (consecutive labels) | "Next cup", "Replay", "Side cups" |
| `MsgArenaCupConfirm0..n` | "The Vale Cup.\nYour party will be set\nto level {argument_signed_number}.\nEnter?{end_now}" |
| `MsgArenaCupLocked` | "That cup is closed.\nClear the one before it." |
| `MsgArenaCupNextRound` | "Round {argument_signed_number} won!\nStep into the circle\nwhen you are ready." |
| `MsgArenaCupGiveUp` | "Round {argument_signed_number}.\nDo you want to give up?" |
| `MsgArenaCupCleared0..n` | "You cleared the Vale Cup!\nCongratulations!" (one a cup, generated) |
| `MsgArenaCupOpened` | "A new cup is open!" |
| `MsgArenaStatsLocked` | "Stat training opens\nat level 99." |
| `MsgArenaNoDjinnYet` | "That Djinni is not\nyours to train yet." |

Smoke: every state of every screen gets a screenshot compared to the stock screen it copies (`UI.md`
design intent 5): the cup prompt, the counter with a locked entry, the confirm, the clear message.

## 7. Balance hooks and risks

### 7.1 A level-10 start

- **Stats** (base, before Djinn, class and gear; `cup-candidates.md` "Party base stats by level"):
  Isaac L10 HP 123, PP 52, Atk 50, Def 23, Agi 47, Luck 5; Mia HP 115, Atk 44, Def 21; L50 is
  roughly HP 450, Atk 187. L20 is HP 207, Atk 85; L99 is HP 750 to 850, Atk 306 to 338.
- **Psynergy tiers** (`cup-candidates.md` "Psynergy by the level a class first teaches it"): levels 1 to 9
  give 40 abilities, 10 to 19 add 38, 20 to 29 add 25, 30 to 39 add 22, 40 to 49 add 2 (Spark Plasma and
  Scourge, PP 40), and **nothing is taught after 40** (the highest teaching level in the
  Reloaded table is 40). So the Psynergy ladder is *complete at bracket 40*. Brackets 50 and up add no
  spells; their power comes from Djinn, gear and stat boosts. This supports the stat shop being the
  level-99 tool.
- **Enemies are strong early.** An enemy moved to the cup level has Atk about 2.5 to 3 times the party's
  base Atk and Def about 1.1 to 1.7 times (`cup-candidates.md` "Early cups": Vermin L1 at L10 is
  Atk 135 vs Isaac 50). Gear and Djinn close the gap; the numbers say a bare party cannot take a Vale
  team at target 10. Hence rung targets ramping from `level - 3` (2.1) and the first cup being short
  and in the Vale shop's tier. Boss HP ratios are huge at low level (Saturos at L10: HP 1633 vs 119,
  13.7x). Treat bosses as the difficulty gate and consider a boss target 2 to 4 under the party level.
- **Coins:** a 12-round cup pays `sum(200 + 100k, k = 0..11) = 9000`; 8 rounds pay 4400; 10 rounds 6500.
  Shop prices run 12 (Herb) to 7500 (Steel Armor); Vale gear 10 to 200. The start purse of 1500 buys
  the Vale stock; the Lalivero stock needs a full cup's winnings. **GUESS** a first-clear bonus of one
  extra cup's pay keeps the shops ahead of the Djinn price (500 each, 28 Djinn = 14000).
- **Djinn.** 28 at 500 is 14000 coins, two to three cups of winnings, so the *unlock* (not the price) is
  what rations Djinn; keep the price.

### 7.2 Bracket fit of the region mobs

At party level 10, regions 1 to 3 have native mobs of level 1 to 7 (margin +3 to +9, "Early cups"),
fine for cup 1. At party level 20 the region 7 and 8 mobs are native L5 to L14 (margin about +6 to +15).
At party 40 the Lighthouse mobs are L23 to L28 (margin +12 to +17) and the bosses L38 to L43 (margin
about 0). So the Atk ratio of mobs to the party is highest in the *low brackets*; the balance pass should
lower rung targets there rather than lowering party levels.

### 7.3 Luck and the stat shop

- **Luck 40 is immunity.** `sArenaRules_EffectRates[luck >= 40]` makes effects 18, 19, 22 to 24, 26 to 28, 30, 34, 39, 41, 43 and 54 a fixed 151 meaning "never" (`arena_rules.c:37-57, 60-71`).
  The rule reads the *target's* luck whatever its side, so a player at luck 40 is immune in PvP too.
- **Where luck comes from.** Base Luck at 99 is only 23 to 26 per character (table in
  `cup-candidates.md`); the shop sells +1 for `(value + 1) * 100` coins up to 99
  (`arena_shop.c:314, 348, 361-362, 379-380`). From 25 to 40 costs `sum(26..40) * 100 = 49,500` coins,
  about five full-cup clears. Unit_Calculate adds Djinn, class and gear to the base (UNKNOWN how
  much, probably a few points), so a base of 35 may already reach 40.
- **Recommendation (decision D6):** cap the *purchasable base* Luck at **30 to 34** (`ArenaStat_Cap`,
  `arena_shop.c:356-366`; today `UNIT_LUCK_MAX` 99), so immunity needs gear and is a build choice.
  For the 99 PvP bracket this bounds the "everything is immune" build. A hard cap on the final value
  would be an engine change (`Unit_Calculate`, UNKNOWN location) and is not recommended.
- **Stat caps** otherwise stand: HP and PP 1999, others 999, steps 20, 10, 5 (`:355-366`, `:341-353`);
  at 99 base HP is 750 to 850, so 1999 is about +1150 HP: roughly 58 purchases at 800 to 1999 coins
  each, about 80,000 coins per character. Plenty of sink for the 99 tier.
- **Stat bonus loss on level change** is discussed in 3.5.

### 7.4 Boss Rush fit

The Boss Rush's rung targets 14, 22, 30, 36, 41, 45 (`arena_ladder.c:55-68`) are absolute. As a side cup
at party level 40 to 50 (decision D3): round 1 (Orc Lord L25 and Lizard King L28 at target 14,
margin -12) is a *downward* scale (enemies lose levels, floored at 70 percent of base HP and others,
`formation.c:200-216`), so it is easier than its numbers; the old note that pressing A does not win
round 1 (GOTCHAS 108-110) predates the Reloaded data port; recheck.
At 99 the ladder is trivially low: move to option D (targets 90 to 99) for the super-boss tier.

### 7.5 The arena's current start

`ArenaBoot_NewGame`: level 50 party, 1500 coins (`arena_boot.c:55-88`; `ARENA_START_LEVEL` 50,
`arena.h:13`). With cups the start should be level 10 and a smaller purse (**GUESS** 500 to 1500) with
cup 1 and only the starter Djinn. Old saves are unaffected (they keep their level until the first
cup). `Unit_LevelUpTo(…, 10)` at boot is cheaper than today.

### 7.6 Risk list

| Risk | Where | Mitigation |
|---|---|---|
| Stat boosts wiped by `SetLevel` | 3.5 item 1 | keep bonus at 99 only, say so in the confirm text |
| Permanent Psynergy bypasses level tiers | 3.5 item 2 | retire the Psynergy shop (D4) |
| Bought gear and Djinn carried into low cups | 3.3 | accept, or "kit reset" (D5) |
| Six-slot overflow in a cup team | 4.2 | `cup-check.py`, static asserts |
| Round-count text and `msgid` allocation | 4 | generic messages, generated per-cup clears |
| Flag range collisions | 5.1 | verified free; list in `arena.h` |
| Old saves (tournament byte 0 or 1, no progress) | 5.2 | ids 0 and 1 unchanged; confirm prompt |
| Locked entries cannot be greyed in the icon row | 6 | use the counter and a "closed" message |
| Enemy Atk caps at 999 near party 80 | 2.3 | only HP, Def, Agi scale above that; design 99 cups around HP |
| Unscripted bosses missing for 8 regions | 1.3 | editorial caps, mark in the cup table |
| Shop rows 1 to 15, 19 to 34 untested in the arena | 5.3 | smoke every row |
| Linked 4v4 brackets | 3.5 item 8 | signature carries the bracket (patch 14) |

## 8. Implementation plan (for the builder)

One patch per step, in order, each building on its own and behind the existing switches
(`ARENA_LADDER`, `ARENA_TRAINING`; add `ARENA_CUPS` in `arena_config.h` for steps 2 onward so the
old behaviour is one switch away). After each: build (check the log for `***`), run the smoke
script(s), look at `build\smoke\shots\sheet.png`, commit in `~/alchemy`, `export-patches.ps1`, update
`CHANGES.md`. Patch numbers continue from 26.

| # | Patch | Content | Smoke scripts (`scripts/smoke/`) |
|---|---|---|---|
| 27 | **Cup table, no change in behaviour** | `arena_cups.c`, `struct ArenaCup`, Gauntlet and Boss Rush converted (4.1), `ArenaLadder_Select` and `ARENA_ROUNDS/HEALS` read the table, generic round messages plus one cleared message per cup, `scripts/cup-check.py` | all existing: `tournaments`, `rungs_rush`, `rush_round`, `heal_round`, `rush_clear`, `clear`, `give_up`, `resume`, `resume_rush` unchanged and green |
| 28 | **ArenaCup_SetLevel** | the function (3.3) in `src/game/game/`, far-call veneer, a debug entry that calls it | `cup_setlevel_down.txt`: boot (L50), call set 10, shot the Characters strip and Psynergy panel (stats and spell list shrink), set 99, shot, set 10 again (compare the same stats); `cup_setlevel_psynergy.txt`: Psynergy shop purchase survives a level drop (documents the pitfall) |
| 29 | **Progress and the attendant's cup menu** | flags 0x7f0, 0x7e8 (`arena.h`), `Next cup / Replay / Side cups` row, the cup counter kind, locked entries, the confirm prompt, level set at series start | `cup_menu.txt` (shots: prompt, counter, locked entry, confirm), `cup_lock.txt` (progress 0: only cup 1 and open side cups; poke 0x0200013E to 3: more open), `cup_start.txt` (Yes sets level; No does not), `cup_old_save.txt` (a pre-cup save: tournament byte 1, progress 0) |
| 30 | **Cup clear and rewards** | progress written at the clear, `firstClearCoins`, `MsgArenaCupOpened`, lose and give-up leave progress alone | `cup_clear.txt` (the test trick of `rush_clear.txt`: start as the easy team, poke the cup byte and win count mid-battle), `cup_clear_twice.txt` (second clear pays nothing), `cup_giveup.txt`, `cup_lose.txt`, `cup_resume.txt` (save mid-cup, `reset`, Continue, give-up prompt, progress byte kept) |
| 31 | **Bracket 10 cups (data)** | cups 1 to 3 with region mobs and caps from `cup-candidates.md`, rung ramps per 2.1 | `cup_rungs_1.txt` ... one shot per rung of cup 1 (reuse the loading pattern of `rungs_rush.txt`), `cup_boss_1.txt` |
| 32 | **Djinn and shop gating** | Djinn panel hides locked Djinn, `ArenaCup_ShopRow`, stat counter locked below 99, optional retirement of the Psynergy counter | `cup_djinn_gate.txt` (progress 0, 3, 11: count of Djinn offered; shot), `cup_shop_rows.txt` (open each of the 34 rows once, shot, check no crash), `cup_stat_locked.txt` (below 99: message; at 99: counter) |
| 33 | **Brackets 20 to 40 (data)** | cups 4 to 11 | `cup_rungs_N.txt` per cup, and `cup_check` (script) as a gate |
| 34 | **Side cups** | convert the Gauntlet and Boss Rush to party levels, add the first themed cup | `cup_side.txt`, `tournaments.txt` updated |
| 35 | **50 to 99 content** | after decision D2 | per cup |
| 36 | **New Game at level 10** | `ARENA_START_LEVEL` 10, purse, zeroed progress | `boot.txt` updated; `cup_newgame.txt` |
| 37 | **PvP brackets (separate agent)** | the lobby asks 50 or 99, `ArenaCup_SetLevel`, signature carries it | link scripts (`link.sh`) at each bracket |
| later | **Trophies** | best result per cup in 0x7d8 and below, shown in the arena and the file list | not in this spec |

Order rationale: 27 changes nothing visible, so it is the safe place to find table and message
mistakes; 28 is isolated and can be tested by calling it from a debug hook before any menu exists;
29 and 30 give a full loop on a single test cup; data (31, 33) and gating (32) come after the loop works.

**Agent hints.** Use `smoke-tester` for 29, 30 and 32 (screens). The `rush_clear.txt` poke
addresses (`0x0200013F` tournament, `0x020004EA` win count) are the pattern for new scripts; the flag
bytes added here are `0x0200013E` and `0x0200013D` (5.1). Do not hand-write the cup table's numbers
that exist in `cup-candidates.md`; copy member ids from it and run `cup-check.py`.

## 9. Decisions needed from the owner

| # | Decision | My recommendation |
|---|---|---|
| D1 | One party level per **bracket** (cups 1 to 3 all at 10, 4 to 6 at 20, ...) as written in 2.2, or one per **cup** in steps of five? | per bracket, as in `CUPS.md` ("brackets of ten") |
| D2 | What fills 50 to 99, and how many cups? (2.3 options A to E) | B at 50, A optional at 60 to 80, C plus D at 99; or only 50 and 99 |
| D3 | Boss Rush and Gauntlet: `requires` and a party level (KEEP_LEVEL today)? | open after cup 4 and cup 9; give them levels 40 and 50 once the line exists |
| D4 | Retire the Psynergy shop (permanent spells bypass level tiers)? | yes, with this change |
| D5 | Bracket "kit" reset (Djinn and gear) at cup start, or keep what was bought? | keep; the unlocks only gate what can be *bought* |
| D6 | Luck cap in the stat shop | base Luck bought up to 30 to 34 |
| D7 | Start purse and whether the first-clear bonus is one cup's pay | 1000 start, bonus = cup's total pay |
| D8 | Cup names (2.2 are candidates) and the thematic side cups wanted first | name by place; first side cup Poison and Debuffs |
| D9 | Region caps with no scripted boss (1.3): hand-built trios as marked **GUESS** | accept, review in the balance pass |

## 10. Unknowns collected

1. Whether bosses are started anywhere other than `Field_RequestBattleFromEncounterTable` (1.2).
2. Sprites, abilities and AI fields of unused enemy rows (2.3 E).
3. Whether the Djinn recovery list stays consistent if `djinnHeld` is edited directly (3.3).
4. Whether equipment has a level requirement (3.3).
5. How `msgid` numbers and `msg_ids.h` are produced for generated messages (4).
6. Whether the arena's `Shop_Run` initialises the artifact stock flags (5.3).
7. How the File Screen could read a save's flags for trophies (5.1).
8. Whether the shop counter greys unaffordable or sold entries (6.1).
9. How much Luck Djinn, class and gear add on top of the base (7.3).
10. What an over-six-slot team looks like on screen (4.2).

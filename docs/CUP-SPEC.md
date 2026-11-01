# Cup framework: specification

Status: **spec only, no gameplay code.** Written 2026-11-01 for the builder agent (plan step 3 in
`CUPS.md`). Source read: `~/alchemy` branch `arena` (`games/tbs`). Every claim carries a file and
line; every guess is marked **GUESS** and every gap **UNKNOWN**. Numbers come from the generated
`cup-candidates.md` (run `scripts/cup-candidates.py`; it reads our enemy table, so levels are the
Reloaded retune). Paths below are relative to `games/tbs` unless they start with `docs/` or `scripts/`.

Contents: 1 Areas, 2 Brackets and cups, 3 Level setting, 4 Data format, 5 Unlock state and saves,
6 Menus, 7 Balance hooks and risks, 8 Implementation plan, 9 Decisions for the owner.

## 0. Summary

- **Area data exists, but not on the formations.** `struct Formation` has no area field
  (`include/battle/formations.h:18-27`). The area lives in the *encounter zones*
  (`src/field/encounter_zones.c`, 104 rows, commented by place), reached by scene from
  `src/field/encounter_rules.s` and by world-map region from
  `src/field/world_map_encounter_rules.c`. Bosses are the `Field_RequestBattleFromEncounterTable(zone, slot)`
  calls in `src/scene`. `scripts/cup-candidates.py` joins these (about 650 lines, run in 1 s) and
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

# Reloaded: the engine changes, decoded

The code changes of the Golden Sun Reloaded TBS patch (v1.83a) and where each stands in
our source. Read from the patch with `scripts/ips-code-diff.py`, `ips-disasm.py` and
`ips-bytes.py` against an unmodified build; written again in C, behind the switches
`ARENA_RULES_*` in `arena_config.h`, on by default. See `RELOADED.md` for the decision and the plan.
Addresses are those of the unmodified English ROM.

The authors fitted small routines into free space (code caves): freed jump-table room in
`Battle_GetEffectBaseSuccessRate`, spare bytes between functions, the last 208 bytes of
the ROM for data. That is why some "changes" read as odd jumps.

## Done, behind switches that default to on (patches 15 to 17)

| Switch | Change | Verified |
|---|---|---|
| `ARENA_RULES_LEVELUP` | A level's stat gain has no random part: `level*d/span - (level-1)*d/span` with `span` 20 (19 below level 20), `d` the growth step of the band. The six stat gains in `Unit_LevelUp`. | **Run through levels 1 to 99 with the patch's growth curves it reproduces the workbook's "Lv99 Character Stats" exactly** for Isaac, Garet, Ivan and Mia (`scripts/levelup-check.py`). Booted: stats are fixed run to run. |
| `ARENA_RULES_AILMENTS` | `Battle_RollEffectSuccess`: chance = base rate + 3 x (caster level / 4 - target luck / 2) + caster's Ailment attribute (+25 for a weakness), succeeds on strictly greater. The base rate comes from two tables of 71 bytes, by effect, **chosen by the target's luck: below 40, or 40 and up (bosses)**; 151 and over is a fixed chance, less 151, so 251 always works and **151 never does**. | Tables read from the patch (ROM end, 0x087fff30 and 0x087fff90); formula read from the disassembly. Compiles, boots; not exercised in a fight yet. |
| `ARENA_RULES_DAMAGE` | In `BattleAbility_ApplyToTarget`, for Psynergy and enemy damage: power += caster's max PP / 8, then power += max PP x power / 1024. A summon's HP share comes from a table (2, 4, 6, 8 percent for 1 to 4 Djinn, by ability id 380 to 401) instead of 3, 6, 9, 12. A party target's class **ward** (percent, kept in `ClassDefinition.weakEffects[3]`, a byte stock never reads) scales the power; a ward of 0 is ignored so stock data is unchanged. | Read from the disassembly; compiles, boots, a Gauntlet battle starts. Damage numbers not checked. |

**Finding: stock-bosses and ailments.** In the second table (luck 40 and up) these are
151, immune: Taint, Poison, Charm, Paralyze, Sleep, Haunt, Condemn, Curse, Reflect,
Severe Blow and the second critical effect; Delude 70, Confuse 50, Bind 55 and the stat
debuffs 75 or 125 still work. So Reloaded **makes bosses immune to most status ailments
on purpose**; the roster of what lands on a boss is a table we can edit freely.

### Patch 17

How each was checked: the rule was read from the patched disassembly (`ips-code-diff.py`,
`ips-disasm.py`, the jump tables with a small table reader), matched to the stock C, written
again, built both ways (all switches 0 and all 1), and the Gauntlet fought headless
(`win.txt`). Where the rule is a small change in a function the compiler lays out the same
way, the built function was also compared **instruction by instruction with the patched
original** (`CountDownAttackStage`, `Defense`, `Resistance`, `Stun`, `Sleep`,
`Battle_AdvanceCounterAndCheckChance`, `Battle_CalculateRecovery`: identical;
`RollCounterEarlyEnd`: the same operations in another order).

| Switch | Change | Verified |
|---|---|---|
| `ARENA_RULES_GUARD` | `REDUCE_BY_GUARD`: Total Defense (and Flash) takes a **third** of the damage, not a tenth. The five damage steps share the macro; the patch changes all five `/10` to `/3`. | Read; the five sites match. Not measured in a fight. |
| `ARENA_RULES_HEAL` | `Battle_CalculateRecovery`: the healer's element power counts at half effect (`Battle_GetElementMultiplier(..., 1)`). `ABILITY_EFFECT_HEAL_PP_7` (Ember): `max PP * 7 / 70`, a tenth, not 7 percent. | Recovery function identical to the patched original. |
| `ARENA_RULES_REVIVE` | The three revival effects restore `maxHp * power / 1000`, plus 1, at most the max HP (power 250 is 25 percent). `ABILITY_FORMULA_EFFECT` revivals no longer also *damage* by their power. Battle (`ability.c`) and the item menu (`use.c`, `Ability_ApplyToTargets`). **Departure:** a power of 0, as the stock data has, keeps the stock amount (full, half, 80 percent; the menu's 70 percent), so stock data is unchanged. In the patch the half and 80 percent effects share Revive's handler. | Read; formula checked against both code paths. Not run in a fight. |
| `ARENA_RULES_EFFECT_IDS` | The patch turns the effect-id jump table into aliases so one handler can have several base chances (the chance tables are by id): 8, 12, 16 (Dull, Impair, Weaken) run the **one-stage** handlers of 9, 13, 17; 36, 37, 38 run the two-stage ones; 21 (Confuse) runs Delude's, 22 (Charm) Paralyze's, 30 (Reflect) Haunt's, 39 Taint's, 40 Poison's, 41 Paralyze's, 43 Haunt's and 54 Condemn's (a "damage, then death" alias). `ArenaRules_EffectHandler` in `ability.c`. **Needs the ability and enemy data** (the patch's abilities use 21, 22, 30, 36 to 41, 43 and 54, and abilities 117 and 129 lose their effects); on stock data Confuse acts as Delude, Charm as Paralyze and Reflect as Haunt. | The 16 changed table entries read from the ROM and matched to the handlers. Not exercised (needs the data). |
| `ARENA_RULES_DURATIONS` | Impact, Guard and Ward (the two-stage raises) last **5** turns, not 7; Luff seals as long as Bind (`psySeal` gets 7, not 16); the curse counts **4**, not 7. | Read; compiled. |
| `ARENA_RULES_STAGES` | A Defense stage is worth 3/16 of the stat (`def * (3 * stage + 16) / 16`; stock `(stage + 8) / 8`); a Resistance stage is worth 15, not 20, in `Unit_Calculate`, in the stat-change messages (`ability.c`) and in the battle status screen. | Read; compiled. |
| `ARENA_RULES_RECOVERY` | The early-recovery roll `BattleUnit_RollCounterEarlyEnd`: `luck - 5 * turns - level / 2 + bias` (stock `luck * 3 - 5 * turns + bias`). New biases: Attack 10 (from 30), Defense 5 (20), Resistance 5 (20), stun 50 (40), sleep 40 (50), Bind 40 (30); delusion 30, confusion 60 and charm 70 unchanged. | Compiled functions identical to the patched original (one reordered). |
| `ARENA_RULES_STATUS` | A haunted unit's share is taken on 103 rolls in 256 (about 40 percent), not 1 in 4. A deluded unit's attack misses on a roll of 0 to 179 of 255 (70 percent, was 60), and a deluded unit **never unleashes** (`RollWeaponUnleash` returns the plain attack). | Read; compiled. |
| `ARENA_RULES_CLASS20` | Class multipliers are in **twentieths** (`stat * multiplier / 20`; stock tenths). Equipment multipliers stay in tenths. **Needs the class data doubled**: with stock data every class stat is halved (seen: Isaac's HP at level 50 falls from 456 to 229). | Read; seen in the smoke run. |
| `ARENA_RULES_CAPS` | Element power and resistance, and PP regeneration, are capped at **255** in `Unit_Calculate` (stock 200). | Read; compiled. |
| `ARENA_RULES_ITEMS` | The stat-boost items (Power Bread, Cookie, Mint, Apple, Hard Nut) give exactly their power: no -1, 0 or +1 roll ("Item Stat-boost Randomness Removal"). | Read; compiled. |
| `ARENA_RULES_SUMMON_TURNS` | **Summons wait their turn.** Summons that cost one or two Djinn are available from the start, the three-Djinn ones from the second turn, the four-Djinn ones from the third (`BattleSummon_UpdateAvailability` masks the mask by 0xff, 0xfff, 0xffff; the count is `BattleWork.arenaTurn`, a byte no stock code names). Not in the changelog. The patch does it in a hook on `Djinn_GetRecoveryTable` with a counter in a free flag byte, plus a hidden copy of the mask; ours masks the stored mask once per turn and keeps no copy. | The counter was read in a battle: 0 on the first turn, 1 after it (`rules_turn.txt`). The masking was not exercised (the test party holds no Djinn). |
| `ARENA_RULES_AILMENTS` (added) | **The Ailment attribute is now summed**: `Unit_Calculate` clears `Unit.unused[0]` and adds equipment effect 24 (`EQUIP_EFFECT_24`, which stock sums into a byte nothing reads) to it. Patch 15 already read it in the success roll. | Read; compiled. Needs item data with effect 24. |

## Not ported

| Where | What | Why |
|---|---|---|
| `Battle_CollectPartyCommands`, `BattleItemMenu_Run`, `BattleDjinnMenu_ShowChangePreview`, `DjinnMenu_ShowCurrentList`, `DjinnMenu_DrawElementList`, `DjinnMenu_DrawStatPreview`, `ItemMenu_DrawItemDetails` | window sizes, columns and a few jump-table words | The patch's "Menu Panels Revamped" layout, tied to its own panel graphics. Our UI follows `UI.md`. |
| `BattleEffect_RunStatBoost`, `BattleEffect_RunDjinnBeams`, `BattleObject_Make`, `BattleEffect_RunTitanBlade` | which resource, sprite or palette is drawn (a helper at 0x080bc338 picks one of 141, 143, 145, 147 by the number of Djinn used; the character sprite table is moved) | Graphics resources the patch brings; nothing to port without them. |
| the Djinn debuff chance and "every non-overworld Djinn can't escape" | **Data**: rate table entries (done in patch 15) and enemy and formation rows | For the data port. |
| unleash and EPA multipliers; Dragon Cloud and Death Leap ignoring 50 percent | **Data**: ability kinds and effects | For the data port. The roll that "may ignore 50 percent of defense" is `Battle_RollEffectSuccess` with the 90 percent table entry (patch 15). |
| Deadbeard's HP and PP regeneration | The patch only raises the PP regeneration cap (CAPS). `UNIT_HP_REGEN_MAX` is 10000 for a byte (`Unit.hpRegen`) and the patch does not change that, so any fix is in the enemy data. | Uncertain: not decoded further. |
| `gBattleSprites`, `gAbilityBattleEffects` (92 bytes), `gFormations`, `gPsynergyIcons` | data tables, indexed by ability, formation and icon | For the data port (the effect-id aliases need `gAbilityBattleEffects` rows for the abilities that use ids 36 to 43 and 54). |

## What the data port must carry for these rules

**Done (patches 18 to 26, 2026-11-01):** everything below is in our tables now, ported by
`scripts/port-reloaded-tables.py` and verified byte for byte against the patched stock ROM
(`scripts/table-check.py`, `docs/CHANGES.md` entries 18 to 26). Two things the port settled:
the class ward is the named field `ClassDefinition.ward` (the old `weakEffects[3]` byte, same
struct size), and the effect ids the aliases need are named `ARENA_EFFECT_*` in
`arena_config.h`. With the data in, a New Game gives the workbook's stats (level 99 equals
its sheet; level 50 is checked in `stats.txt`).
The original checklist, kept for the Lost Age port:

- Ability rows: effect ids as in the patch (see EFFECT_IDS), revival power in tenths of a
  percent, the stat-item amounts.
- Class rows: the six multipliers doubled (CLASS20), vulnerabilities and the ward in
  `weakEffects` by the *aliased* ids.
- Item rows: effect 24 for the Ailment attribute.
- Enemy rows: weaknesses by aliased id, regeneration values.
- The lobby signature (patch 14) should change when these rules or the data do.

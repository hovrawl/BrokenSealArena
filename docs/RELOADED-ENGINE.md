# Reloaded: the engine changes, decoded

The code changes of the Golden Sun Reloaded TBS patch (v1.83a) and where each stands in
our source. Read from the patch with `scripts/ips-code-diff.py`, `ips-disasm.py` and
`ips-bytes.py` against an unmodified build; written again in C, behind the switches
`ARENA_RULES_*` in `arena_config.h`, on by default. See `RELOADED.md` for the decision and the plan.
Addresses are those of the unmodified English ROM.

The authors fitted small routines into free space (code caves): freed jump-table room in
`Battle_GetEffectBaseSuccessRate`, spare bytes between functions, the last 208 bytes of
the ROM for data. That is why some "changes" read as odd jumps.

## Done (patches 15 and 16), behind switches that default to on

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

## Located, not yet decoded or written

Addresses are in `BattleAbility_ApplyToTarget` (0x080bbb0c) unless named.

| Where | What changed | Notes |
|---|---|---|
| 0x080bbfd4 | a heal's scaling: stock halves one case and divides by 10 in another; new `2x / 4` or `2x / 6` | healing formula ("Healing fixed", "Base power of healing spells increased") |
| 0x080bc0ee, 0x080bc276, 0x080bc3fe, 0x080bc5d6 | `x / 10` becomes `x / 3` | four places, probably the multiplier of an attack or effect; need the surrounding source |
| 0x080bc9e8 | `x * 7 / 100` becomes `/ 70` | one place |
| 0x080bcce8 on | revive amount: `maxHp x power / 1000 + 1`, capped at max HP, in place of full, half and 80 percent; the other revive cases jump into code caves | "Water of Life revives to 25% HP" |
| 0x080bcdc8, 0x080bce1a, 0x080bce6a, 0x080bcebe | `x * 20` becomes `x * 15` | four places in the effect chain |
| 0x080bcf2c, 0x080bcf9c, 0x080bd21e | counters set to 5, 7 (from 16) and 4 (from 7) | status and stat-change durations |
| 0x080bd33e | a random test `(r & 3) == 0` (25 percent) becomes `(r & 255) <= 102` (about 40 percent) | which effect needs reading |
| `Ability_ApplyToTargets` (0x080a9f10) | a random call replaced, the heal-by-half and revive cases rewritten like the above | item and field path |
| `Unit_Calculate` (0x08077???) | 146 bytes in 18 places | stat caps, the Ailment attribute, regeneration |
| `Battle_CollectPartyCommands`, `BattleObject_Make`, `BattleUnit_RollCounterEarlyEnd`, `BattleEffect_RunStatBoost`, `BattleEffect_RunDjinnBeams`, `BattleDjinnMenu_ShowChangePreview`, `Battle_ProcessTurnEnd`, menus | a few bytes each | Djinn debuffs, Djinn escape, UI |

Next steps in order: read the surrounding source for each row and match it, write the
rows as switches (`ARENA_RULES_HEAL`, `_REVIVE`, `_DURATIONS`, and so on), then the Ailment
attribute in `Unit_Calculate` with the item table.

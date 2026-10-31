# Golden Sun Reloaded: the author's design notes, and what they mean for the arena

Summary (not a copy) of the first post of the mod's release thread (forum.goldensunhacking.net,
topic 2779), read 2026-11-01 because the changelog is only a delta between versions. The
author is credited there as the mod's maker; their post explains the intent behind the
numbers. This note records the intent so our port keeps it.

## Philosophy

- **More options, then more difficulty.** The goal is to make weak strategies viable (item
  classes, debuffs, unleashing mages, Djinn that attack and revive, caster classes that
  attack) and to remove the dominant one: **summon rushing** (all Djinn on standby, a
  barrage of summons on turns 0 and 1) and Megiddo. Difficulty is secondary, "to give
  players a reason to try the strategies", aimed at players who know the game.
- Everything is gameplay, nothing story. It affects both games and they link.

## The rules, with the author's reasons (and our switch)

| Rule | The author's statement | Why | Ours |
|---|---|---|---|
| Base damage | damage = (base power + max PP / 8) x element factor x (1 + max PP / 1024) | the game has no magic offence stat; max PP becomes it, so mages out-cast warriors and growth is smooth; gear for max PP vs PP recovery becomes a real choice | `ARENA_RULES_DAMAGE` |
| Spell PP costs | recalculated by a custom formula that weights power more than range; group heals and revives cost much more | group healing was badly under-costed | data |
| Healing | healed = power x (((element power - 100) / 2 + 100) / 100); element power counts half | element power was twice as strong for healing as for attack; boosting it helped casters and healers unevenly | `ARENA_RULES_HEAL` |
| Revive | every revive works; Revive, Raise, Lich, Phoenix restore 50 percent HP; Water of Life 25 percent | revive at full HP made it better to die and be revived than to heal | `ARENA_RULES_REVIVE` |
| Ailment chance | ((caster level / 4 - target luck / 2) x 3 + base + Ailment bonuses + 25 weakness) x area multiplier | elemental level and luck never grew, so debuffs never worked on bosses; levels now matter, and luck grows with level | `ARENA_RULES_AILMENTS` |
| Recovery from an ailment | luck - level / 2 - turns x 5 + base | the longer it lasts the likelier it ends | `ARENA_RULES_RECOVERY` |
| Luck of 40 or more | immune to stun and sleep, in addition to the usual immunities (poison, venom, haunt, death) | "stunning or sleeping bosses can only be OP or irrelevant"; poison, venom and haunt would force a fully defensive game; but debuffs stay useful on bosses | `sArenaRules_EffectRates` second table |
| Stat stages | defense buff x1.75 at the top (was x1.1875), debuff down to x0.25 (was x0.8125); resistance +-15/30, cap +-60 | defense buffs were the weakest; resistance buffs the strongest | `ARENA_RULES_STAGES` |
| Durations | the stronger (single-target and Djinn) buffs and debuffs last 5 turns, weaker multi-target ones 7 and cost more; haunt triggers at 40 percent; delusion stops unleashing and raises misses; death curse counts 4 | a downside for the strong ones, so the weak ones stay worth using; bosses are alone, so multi-target debuffs last longer | `ARENA_RULES_DURATIONS`, `_STATUS` |
| Summons | HP share about 2 to 2.5 percent a Djinni (was 3); strongest summons wait: 3-Djinn ones after the first turn, 4-Djinn after the second, and so on up to 10 Djinn after the sixth | summon rushing made every boss a joke; with turn gating you will not live long enough with most Djinn on standby | `ARENA_RULES_DAMAGE`, `_SUMMON_TURNS` |
| Level-up | no random part; luck grows; characters have more innate HP and Djinn give about half the HP | so setting Djinn costs less when you summon; luck-based immunity cannot be manipulated by RNG | `ARENA_RULES_LEVELUP` |
| Classes | multipliers in 5 percent steps; a magic resistance stat (WRD, damage taken from base-damage attacks; 95 percent WRD means 5 percent more damage); a fourth three-element class for everyone; item classes can rise a tier with three Djinn of one new element; Jenna and Piers remade | mages had no magic defence; the missing class line left a gap in Djinn combinations | `CLASS20`, ward in `weakEffects[3]` |
| Weapons | categories: long swords standard; light blades less attack, more agility and defense; axes more attack, less defense; maces less attack, less unleash rate, more max HP, power and Ailment; staves much less attack, more unleash rate, max PP and power; ankhs the same with luck and Ailment | in vanilla weapons differed only in name | data |
| Unleashes | rate 30 percent; every attack unleash and EPA uses a multiplier (no flat added damage); staff unleashes are base-damage type, so mages unleash well | added damage does not scale | data |
| Equipment | the "Golden Rule": anything found or bought is stronger than anything of its type earlier and weaker than anything later; the Ailment attribute raises ailment chance by its value, like Criticals do for unleashes | progression gear | data, `AILMENTS` |
| Enemies | every enemy stronger; casters get max PP of at least level x5 so the PP multiplier helps them; bosses debuffable; Break used less so buffing is not discouraged; bosses retuned (v1.83: less spongy) | difficulty near vanilla TLA hard mode | data |
| Djinn | most improved, the strongest nerfed; Flash reduces damage 66 percent (was 90), Shade 50 (was 60); Flora lowers resistance instead of sleep; Reflux multi-target; Vine, Mud, Gasp and Fury deal base damage; Ember restores 10 percent PP, Ether 35, Aroma 12.5; Balm and Spark revive to 50 percent; Crystal heals 60 percent; Djinn debuff chances up | rebalance | data |

## What this explains (and the earlier uncertainty)

- **Summon turn gating and "a deluded unit cannot unleash" are intended**, not accidents:
  both are in the post. The sub-agent's remark that they are "not in the changelog" is
  because the changelog is only a delta.
- **Luck and the stat shop.** Luck 40 gives immunity to stun, sleep and the other status
  effects in the second rate table, for friend and foe alike. A character at level 99 has
  luck of about 23 to 26 in the data, so 40 is out of reach by levels; **our arena's stat
  shop can sell Luck**, so a player could buy immunity. Decide a cap for Luck in the shop
  (or let it be a deliberate strategy). In 4v4 PvP, immunity at 40 matters more.
- **Summon gating in the arena.** A turn counter exists only in a battle, so it also gates
  a 4v4 linked fight, which suits "no summon rush" in PvP, but a short Boss Rush fight
  with a few turns will rarely get 4-Djinn summons. Worth watching in balance.
- **Class ward** makes mages and warriors take different damage from spells; in PvP the
  class pairs matter.
- **Reloaded wants players to start from level 1**; our level 50 start skips its
  progression curve (the Golden Rule for gear, the level-based debuff chance), so the
  arena must supply its own: this is what the balance pass is for.
- **Psynergy: the last is learnt at 42**, so a level 50 start opens everything.
- Equipment tiers and treasure, shops and drops (TLA) are story progression: ignore.

## Caveats

- Only the first post (page 1 of 48) was read; later pages hold fixes and discussion. The
  FAQ notes the patch must be applied to a clean ROM and that the PSYNERGY "Move" being
  Earth tells a patched ROM apart.
- The thread's `topic=2779.0` was fetched over plain HTTP because the forum's HTTPS
  certificate has expired; the saved page is under `build/` (git-ignored).

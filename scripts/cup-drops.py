#!/usr/bin/env python3
"""Lists the equipment that the enemies of each cup drop in the story game.

Usage: cup-drops.py [GAME_DIR]   (default ~/alchemy/games/tbs)

An enemy row of enemy_table.c can carry one drop (`.item`, with `.itemChance`: the chance
is 1 in 2 to the power itemChance - 1). Joined with the cups of cupdata.py, this says which
gear a cup's fights would have dropped, to offer as the round's first-win reward in place of
consumables. Only equipment is listed (weapons, armour, shields, helms, boots, rings and
shirts).
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cupdata  # noqa: E402

game = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/alchemy/games/tbs")
EQUIP = {"ITEM_TYPE_WEAPON", "ITEM_TYPE_ARMOR", "ITEM_TYPE_SHIELD", "ITEM_TYPE_HELM",
         "ITEM_TYPE_BOOTS", "ITEM_TYPE_RING", "ITEM_TYPE_SHIRT"}

types = {}   # ITEM_CONSTANT -> (name, type); the constant is the row's comment, upper-cased
rows = re.split(r"\n    // ([^\n]*)\n    \{", open(game + "/src/game/item_table.c").read())
for index in range(1, len(rows), 2):
    t = re.search(r"\.type = (ITEM_TYPE_\w+)", rows[index + 1])
    const = "ITEM_" + re.sub(r"[^A-Z0-9]+", "_", rows[index].upper().replace("'", "")).strip("_")
    types[const] = (rows[index], t.group(1) if t else "")

enemies = {}
rows = re.split(r"\n    // ([^\n]*)\n    \{", open(game + "/src/game/enemy_table.c").read())
for index in range(1, len(rows), 2):
    body = rows[index + 1]
    item = re.search(r"\.item = (ITEM_\w+)", body)
    chance = re.search(r"\.itemChance = (\d+)", body)
    enemies[(index - 1) // 2] = (rows[index], item.group(1) if item else None, int(chance.group(1)) if chance else 0)

for cup in cupdata.CUPS:
    print("## %s" % cup.name)
    for number, rnd in enumerate(cup.rounds, 1):
        for enemy, count in rnd.team:
            name, item, chance = enemies.get(enemy, ("?", None, 0))
            if item is None or item not in types:
                continue
            label, kind = types[item]
            if kind in EQUIP:
                print("  round %d  %-18s drops %-24s (%s, 1 in %d)" % (number, name, item, label, 2 ** max(chance - 1, 0)))

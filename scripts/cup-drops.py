#!/usr/bin/env python3
"""Lists the equipment that the enemies of each cup's story stretch drop in the story game.

Usage: cup-drops.py [GAME_DIR]   (default: the working copy, see alchemy_dir.py)

An enemy row of enemy_table.c can carry one drop (`.item`, with `.itemChance`: the chance
is 1 in 2 to the power itemChance - 1). Two lists per cup (only equipment: weapons, armour,
shields, helms, boots, rings and shirts):
  round enemies   the enemies of the cup's own rounds (cupdata.py)
  stretch mobs    the random mobs of the encounter zones met in the cup's stretch of the story
                  (cupstretch.py: the REGIONS of cup-candidates.py), which is what the story
                  would have dropped on the way from the previous cup's boss to this one's.
"""
import importlib.util
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import alchemy_dir  # noqa: E402
import cupdata  # noqa: E402
import cupstretch  # noqa: E402

game = sys.argv[1] if len(sys.argv) > 1 else alchemy_dir.GAME
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


def candidates():
    spec = importlib.util.spec_from_file_location("cupcand", os.path.join(HERE, "cup-candidates.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.argv = [sys.argv[0], game]
    spec.loader.exec_module(mod)
    return mod


def stretch_enemies(mod, regions):
    """enemy ids of the random mobs of the regions' encounter zones"""
    fo, zo = mod.parse_formations(), mod.parse_zones()
    ids = set()
    for r in regions:
        for z in mod.REGIONS[r - 1][1]:
            for fid in zo[z]["forms"]:
                if 0 <= fid < len(fo):
                    ids.update(fo[fid]["members"])
    return ids


def drop_line(enemy):
    name, item, chance = enemies.get(enemy, ("?", None, 0))
    if item is None or item not in types:
        return None
    label, kind = types[item]
    if kind in EQUIP:
        return "%-18s drops %-24s (%s, 1 in %d)" % (name, item, label, 2 ** max(chance - 1, 0))
    return None


def main():
    mod = candidates()
    for cup in cupdata.CUPS:
        print("## %s" % cup.name)
        for number, rnd in enumerate(cup.rounds, 1):
            for enemy, count in rnd.team:
                line = drop_line(enemy)
                if line:
                    print("  round %d  %s" % (number, line))
        info = dict(cupstretch.STRETCH).get(cup.short)
        if info:
            for enemy in sorted(stretch_enemies(mod, info["regions"])):
                line = drop_line(enemy)
                if line:
                    print("  stretch  #%-3d %s" % (enemy, line))


main()

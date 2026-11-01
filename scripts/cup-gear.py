"""Lists the dungeons' chests and gifts by cup, for the gear rewards (docs/CUP-SPEC.md).

Run in WSL:  python3 scripts/cup-gear.py [--missing] [--equip]
Reads src/scene/*.c in ~/alchemy/games/tbs: every chest trigger
  { EXAMINE_TRIGGER(EXAMINE_CHEST), id, FLAG, FIND_ITEM(ITEM_X) }
(TreasureSpot actors, include/field/field_work.h) and every
PartyInventory_GiveItem / Party_GiveItem(ITEM_X, ...) call in scene code (boss and story gifts).
Joins them with the item table (name, type, price), assigns each scene to the
cup whose story stretch holds it (scripts/cupstretch.py: the previous cup's boss dungeon up
to this cup's), lists them in story order and marks the items cupdata.py already
gives as a reward. --missing lists only the items not yet given by any cup; --equip only equipment.
Coins, Psynergy Stones and Mimics are listed apart."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cupdata as D
import cupgame as G

import cupstretch as S

EQUIP = {"weapon", "armor", "shield", "helm", "boots", "ring", "shirt"}
CUP_SCENES = [(c, i["scenes"]) for c, i in S.STRETCH]
cup_of = S.cup_of


def item_table():
    text = G.read("src/game/item_table.c")
    body = text[text.index("gItem_DefinitionTable[] = {"):]
    out = []
    for m in re.finditer(r"^    // ([^\n]*)\n    \{(?:0\},|\n(.*?)^    \},)", body, re.S | re.M):
        blk = m.group(2) or ""
        price = re.search(r"\.price = (\d+)", blk)
        typ = re.search(r"\.type = ITEM_TYPE_(\w+)", blk)
        out.append((m.group(1).strip(), int(price.group(1)) if price else 0,
                    typ.group(1).lower() if typ else ""))
    return out


item_ids = G.item_ids


def main():
    items = item_table()
    ids = item_ids()
    given = set()
    for cup in D.CUPS:
        for rd in cup.rounds:
            for rw in rd.rewards:
                if rw[0] == "item":
                    given.add(rw[1])
    only_missing = "--missing" in sys.argv
    only_equip = "--equip" in sys.argv
    scene_dir = os.path.join(G.GAME, "src/scene")
    found = {}      # cup -> list of (scene, kind, id, item)
    others = []
    for fn in sorted(os.listdir(scene_dir)):
        if not fn.endswith(".c") or fn.startswith("arena_"):
            continue
        scene = fn[:-2]
        text = open(os.path.join(scene_dir, fn), encoding="utf-8", errors="replace").read()
        cup = cup_of(scene)
        for m in re.finditer(r"\{\s*EXAMINE_TRIGGER\((\w+)\),\s*(\w+),\s*(\w+),\s*(FIND_\w+)(?:\(([^)]*)\))?\s*\}", text):
            kind, tid, flag, find, arg = m.groups()
            if find == "FIND_ITEM":
                found.setdefault(S.ITEM_STRETCH.get(arg, cup), []).append(
                    (scene, "chest" if kind == "EXAMINE_CHEST" else kind.lower(), tid, arg))
            else:
                others.append((cup, scene, tid, find + ("(%s)" % arg if arg else "")))
        for m in re.finditer(r"(?:PartyInventory|Party)_GiveItem\((ITEM_\w+)", text):
            line = text.count("\n", 0, m.start())
            fnname = ""
            for fm in re.finditer(r"^\w[\w \*]*\b(\w+)\(", text[:m.start()], re.M):
                fnname = fm.group(1)
            found.setdefault(S.ITEM_STRETCH.get(m.group(1), cup), []).append((scene, "gift in " + fnname, line + 1, m.group(1)))
    total = 0
    for cup in [c for c, _ in CUP_SCENES] + ["(none)"]:
        rows = found.get(cup, [])
        if only_missing:
            rows = [r for r in rows if r[3] not in given]
        if only_equip:
            rows = [r for r in rows if r[3] in ids and ids[r[3]] < len(items) and items[ids[r[3]]][2] in EQUIP]
        rows = sorted(set(rows), key=lambda r: (S.order_of(r[0]), r[1], r[2]))
        if not rows:
            continue
        print("## %s" % cup)
        for scene, kind, tid, item in rows:
            idx = ids.get(item)
            name, price, typ = items[idx] if idx is not None and idx < len(items) else ("?", 0, "?")
            print("  %-28s %-22s %4s  %-22s %-24s %-8s %5d %s" % (
                scene, kind, tid, item, name, typ, price, "GIVEN" if item in given else ""))
            total += 1
    print("\n%d item rows%s" % (total, " not yet given by a cup" if only_missing else ""))
    if not only_missing:
        print("Not items: %d chests/triggers hold coins, a Psynergy Stone, a message or a Mimic (not listed)" % len(others))


if __name__ == "__main__":
    main()

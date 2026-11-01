"""Lists the dungeons' chests and gifts by cup, for the gear rewards (docs/CUP-SPEC.md).

Run in WSL:  python3 scripts/cup-gear.py [--missing]
Reads src/scene/*.c in ~/alchemy/games/tbs: every chest trigger
  { EXAMINE_TRIGGER(EXAMINE_CHEST), id, FLAG, FIND_ITEM(ITEM_X) }
(TreasureSpot actors, include/field/field_work.h) and every
PartyInventory_GiveItem(ITEM_X, ...) call in scene code (boss and story gifts).
Joins them with the item table (name, type, price), assigns each scene to the
cup that owns its region (CUP_SCENES) and marks the items cupdata.py already
gives as a reward. --missing lists only the items not yet given by any cup.
Coins, Psynergy Stones and Mimics are listed apart."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cupdata as D
import cupgame as G

# scene file (a prefix of its name) -> the cup that owns the region, by cup short name
CUP_SCENES = [
    ("Tret", ["sol_sanctum", "vale_kradens", "vale_plaza", "vale_prologue", "vale.c", "cottage_rooms_a",
              "goma_cave", "kolima", "log_rooms_c", "tret_tree", "tree_rooms", "kolima_forest"]),
    ("Mercury", ["bilibin", "cottage_rooms_c", "mercury_lighthouse"]),
    ("Mogall", ["imil", "fuchin", "mogall_forest"]),
    ("Altin", ["altin", "lamakan", "vale_cave", "vault_cave", "alpine_crossing", "vault", "log_rooms_a",
               "log_rooms_b", "lacquer_rooms_b", "xian"]),
    ("Tolbi", ["tolbi", "ship_rooms", "altmiller", "colosseum", "kalay", "stone_rooms"]),
    ("Lunpa", ["gondowan", "lunpa", "hammet", "suhalla", "west_lunpa", "rock_rooms", "stucco"]),
    ("Lighthouse", ["babi", "tunnel_ruins", "venus_lighthouse"]),
    ("Crossbone", ["crossbone", "lalivero", "timber_rooms"]),
]


def cup_of(scene):
    for cup, prefixes in CUP_SCENES:
        for p in prefixes:
            if scene.startswith(p) or scene + ".c" == p:
                return cup
    return "(none)"


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
    scene_dir = os.path.join(G.GAME, "src/scene")
    found = {}      # cup -> list of (scene, kind, id, item)
    others = []
    for fn in sorted(os.listdir(scene_dir)):
        if not fn.endswith(".c") or fn.startswith("arena_"):
            continue
        scene = fn[:-2]
        text = open(os.path.join(scene_dir, fn), encoding="utf-8", errors="replace").read()
        cup = cup_of(scene)
        for m in re.finditer(r"\{\s*EXAMINE_TRIGGER\((\w+)\),\s*(\d+),\s*(\w+),\s*(FIND_\w+)(?:\(([^)]*)\))?\s*\}", text):
            kind, tid, flag, find, arg = m.groups()
            if find == "FIND_ITEM":
                found.setdefault(cup, []).append((scene, "chest" if kind == "EXAMINE_CHEST" else kind.lower(), int(tid), arg))
            else:
                others.append((cup, scene, int(tid), find + ("(%s)" % arg if arg else "")))
        for m in re.finditer(r"PartyInventory_GiveItem\((ITEM_\w+)", text):
            line = text.count("\n", 0, m.start())
            fnname = ""
            for fm in re.finditer(r"^\w[\w \*]*\b(\w+)\(", text[:m.start()], re.M):
                fnname = fm.group(1)
            found.setdefault(cup, []).append((scene, "gift in " + fnname, line + 1, m.group(1)))
    total = 0
    for cup in [c for c, _ in CUP_SCENES] + ["(none)"]:
        rows = found.get(cup, [])
        if only_missing:
            rows = [r for r in rows if r[3] not in given]
        if not rows:
            continue
        print("## %s" % cup)
        for scene, kind, tid, item in sorted(rows):
            idx = ids.get(item)
            name, price, typ = items[idx] if idx is not None and idx < len(items) else ("?", 0, "?")
            print("  %-28s %-22s %4d  %-22s %-24s %-8s %5d %s" % (
                scene, kind, tid, item, name, typ, price, "GIVEN" if item in given else ""))
            total += 1
    print("\n%d item rows%s" % (total, " not yet given by a cup" if only_missing else ""))
    if not only_missing:
        print("Not items: %d chests/triggers hold coins, a Psynergy Stone, a message or a Mimic (not listed)" % len(others))


if __name__ == "__main__":
    main()

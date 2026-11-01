#!/usr/bin/env python3
"""Build docs/cup-candidates.md from the game's own tables (nothing copied by hand).

Usage (in WSL):  python3 scripts/cup-candidates.py [GAME_DIR] [OUT.md]
GAME_DIR defaults to the working copy (see alchemy_dir.py).

Reads:
  src/game/enemy_table.c        enemy rows (index = Formation.memberIds value), name = row comment
  src/battle/formations.c       gFormations (380 rows; index = formation id)
  src/field/encounter_zones.c   gEncounterZones (104 zones: level, formations, weights)
  src/field/encounter_rules.s   which scene (and entrance) uses which zone
  src/field/world_map_encounter_rules.c   which world-map region/terrain uses which zone
  src/scene/*.c                 scripted battles: Field_RequestBattleFromEncounterTable(zone, slot)
                                and Djinn: Field_RequestDjinnBattle(actor, DJINNI_X)
  src/game/djinn_table.c        Djinn names (row comment)

The ONLY editorial layer is REGIONS below (which zones make a story region and in what
order); everything else is read from the source. Re-run after the tables change.
"""
import os
import re
import sys
from collections import OrderedDict, defaultdict

from alchemy_dir import GAME as _DEFAULT_GAME  # noqa: E402
GAME = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else _DEFAULT_GAME)
OUT = sys.argv[2] if len(sys.argv) > 2 else None


def read(rel):
    with open(os.path.join(GAME, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


# --------------------------------------------------------------------------- enemies
def parse_enemies():
    text = read("src/game/enemy_table.c")
    body = text[text.index("gEnemy_Definitions[] = {"):]
    rows = []
    # each row: "    // Name\n    {\n ... \n    },"
    for m in re.finditer(r"^    // ([^\n]*)\n    \{(.*?)^    \},?", body, re.S | re.M):
        name, blk = m.group(1).strip(), m.group(2)

        def num(field, default=0):
            mm = re.search(r"\.%s = (-?\d+)" % field, blk)
            return int(mm.group(1)) if mm else default

        rows.append(dict(name=name, level=num("level"), hp=num("hp"), atk=num("atk"),
                         dfn=num("def"), agi=num("agi"), luck=num("luck"),
                         exp=num("experience"), coins=num("coins")))
    assert len(rows) == 165, "enemy rows: %d" % len(rows)
    return rows


# ------------------------------------------------------------------------- formations
def parse_formations():
    text = read("src/battle/formations.c")
    body = text[text.index("gFormations[] = {") + len("gFormations[] = {"):]
    forms = []
    i = 0
    # top-level "{...}," items
    depth = 0
    start = None
    for k, ch in enumerate(body):
        if ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                forms.append(body[start:k + 1])
        if depth < 0:
            break
    out = []
    for blk in forms:
        def arr(field):
            mm = re.search(r"\.%s = \{([^}]*)\}" % field, blk)
            if not mm:
                return []
            return [int(x) for x in mm.group(1).replace(" ", "").split(",") if x != ""]
        out.append(dict(members=arr("memberIds"), mn=arr("minimumCounts"), mx=arr("maximumCounts")))
    return out


# ----------------------------------------------------------------------------- zones
def parse_zones():
    text = read("src/field/encounter_zones.c")
    body = text[text.index("gEncounterZones[] = {"):]
    # zone 0 is written "{0}," on one line (no encounters); the others span lines
    zones = [dict(comment="No encounters", rate=0, level=0, forms=[], weights=[])]
    for m in re.finditer(r"^    // ([^\n]*)\n    \{\n(.*?)^    \},", body, re.S | re.M):
        comment, blk = m.group(1).strip(), m.group(2)

        def num(f):
            mm = re.search(r"\.%s = (\d+)" % f, blk)
            return int(mm.group(1)) if mm else 0

        def arr(f):
            mm = re.search(r"\.%s = \{([^}]*)\}" % f, blk)
            return [int(x) for x in mm.group(1).replace(" ", "").split(",") if x] if mm else []
        zones.append(dict(comment=comment, rate=num("rate"), level=num("level"),
                          forms=arr("enemies"), weights=arr("weights")))
    return zones


def parse_rules():
    """zone -> list of (scene, entrance) from encounter_rules.s"""
    text = read("src/field/encounter_rules.s")
    z = defaultdict(list)
    for m in re.finditer(r"^\s*encounter_rule (\w+), (-?\d+), (-?\d+), (\d+), (\d+)", text, re.M):
        z[int(m.group(5))].append((m.group(1), int(m.group(2))))
    return z


def parse_worldmap_rules():
    text = read("src/field/world_map_encounter_rules.c")
    arr = text[text.index("gWorldMap_EncounterRules[132] = {"):]
    arr = arr[:arr.index("};")]
    nums = [int(x) for x in re.findall(r"-?\d+", arr.split("{", 1)[1])]
    rows = [nums[i:i + 4] for i in range(0, len(nums) - 3, 4)]
    return [r for r in rows if r[0] != -1]


# ----------------------------------------------------------------------- scene scans
def scan_scenes():
    """scripted battles and Djinn battles with their enclosing function"""
    base = os.path.join(GAME, "src/scene")
    battles = []
    djinn = []
    for fn in sorted(os.listdir(base)):
        if not fn.endswith(".c"):
            continue
        t = read("src/scene/" + fn)
        # enclosing function = last line matching "^static void Name(" or "^void Name(" before the call
        for m in re.finditer(r"Field_RequestBattleFromEncounterTable\(\s*([A-Z_0-9]+|\d+)\s*,\s*([^;]*?)\);", t, re.S):
            pre = t[:m.start()]
            fm = list(re.finditer(r"^(?:static )?(?:void|s32) (\w+)\(", pre, re.M))
            battles.append((fn[:-2], fm[-1].group(1) if fm else "?", m.group(1),
                            re.sub(r"\s+", " ", m.group(2)).strip()))
        for m in re.finditer(r"Field_RequestDjinnBattle\([^,]*,\s*(DJINNI_\w+)\)", t):
            djinn.append((fn[:-2], m.group(1)))
    return battles, djinn


def parse_djinn():
    text = read("src/game/djinn_table.c")
    body = text[text.index("gDjinn_DefinitionTable[] = {"):]
    return [m.group(1).strip() for m in re.finditer(r"^    // ([^\n]*)\n    \{", body, re.M)]


def parse_djinn_ids():
    t = read("include/djinn_ids.h")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"(DJINNI_\w+) = (\d+)", t)}


def parse_zone_consts():
    t = read("include/module/field/field_sequence.h")
    d = {m.group(1): int(m.group(2)) for m in re.finditer(r"(ENCOUNTER_ZONE_\w+) = (\d+)", t)}
    return d



def parse_small():
    """isSmall per battle sprite index (enemy row + ENEMY_ID_FIRST = 8)"""
    text = read("src/battle/battle_sprites.c")
    body = text[text.index("gBattleSprites[] = {"):]
    blocks = re.findall(r"^    \{\n(.*?)^    \},", body, re.S | re.M)
    assert len(blocks) >= 172, "battle sprites: %d" % len(blocks)
    return [".isSmall = 1" in b for b in blocks]


def parse_characters():
    """growth curves per character: [hp, pp, atk, def, agi, luck], each six points"""
    text = read("src/game/character_table.c")
    body = text[text.index("gCharacter_DefinitionTable[] = {"):]
    out = []
    for m in re.finditer(r"^    // [^\n]*\n    \{(?:0\},|\n(.*?)^    \},)", body, re.S | re.M):
        blk = m.group(1) or ""
        curves = []
        for f in ("hp", "pp", "atk", "def", "agi", "luck"):
            mm = re.search(r"\.%s = \{([^}]*)\}" % f, blk)
            curves.append([int(x) for x in mm.group(1).split(",")] if mm else [0] * 6)
        out.append(curves)
    return out


# ------------------------------------------------------------------ items and shops
def parse_items():
    text = read("src/game/item_table.c")
    body = text[text.index("gItem_DefinitionTable[] = {"):]
    out = []
    for m in re.finditer(r"^    // ([^\n]*)\n    \{(?:0\},|\n(.*?)^    \},)", body, re.S | re.M):
        blk = m.group(2) or ""
        price = re.search(r"\.price = (\d+)", blk)
        typ = re.search(r"\.type = ITEM_TYPE_(\w+)", blk)
        out.append(dict(name=m.group(1).strip(), price=int(price.group(1)) if price else 0,
                        type=typ.group(1).lower() if typ else ""))
    assert len(out) == 324, "item rows: %d" % len(out)
    return out


def parse_stock():
    text = read("src/shop/shop/stock.c")
    body = text[text.index("sStockTable[SHOP_STOCK_ROWS][SHOP_STOCK_COLUMNS] = {"):]
    body = body[:body.index("};")]
    rows = []
    for m in re.finditer(r"\{\s*([^{}]*?)\s*\},", body, re.S):
        nums = [int(x) for x in re.findall(r"-?\d+", m.group(1))]
        if len(nums) == 33:
            rows.append(nums)
    return rows


# the town of each stock row (Shop_Run calls in src/scene; the scene file is named)
SHOP_ROWS = {1: "Vale (cottage_rooms_a)", 4: "Vault (log_rooms_b)", 7: "Bilibin (cottage_rooms_c)",
             10: "Imil (imil)", 13: "Kolima (log_rooms_c)", 16: "Xian (lacquer_rooms_b)",
             19: "Altin (altin)", 22: "Kalay (kalay)", 25: "Lunpa items (rock_rooms)",
             26: "stucco_rooms_b", 29: "Lunpa weapons (rock_rooms)", 30: "Lunpa armor (rock_rooms)",
             31: "Suhalla (timber_rooms_a)", 32: "Lalivero (timber_rooms_bc)"}


def parse_class_abilities():
    """ability id -> list of (level, class) from class_table.c"""
    text = read("src/game/class_table.c")
    blocks = re.split(r"\n    // ([^\n]*)\n    \{", text)
    got = defaultdict(list)
    for i in range(1, len(blocks), 2):
        cname, cbody = blocks[i], blocks[i + 1]
        for ab, lv in re.findall(r"\.ability = (\d+), \.level = (\d+)", cbody):
            got[int(ab)].append((int(lv), cname))
    return got


def parse_ability_names():
    po = read("text/en.po")
    msgs = {int(i): t for i, t in re.findall(r'msgid "(\d+)"\nmsgstr "([^\n]*)"', po)}
    first = int(re.search(r'msgctxt "MsgAbilityName"\nmsgid "(\d+)"', po).group(1))
    return {n: msgs.get(first + n, "?") for n in range(519)}


def parse_ability_pp():
    table = read("src/game/ability_table.c")
    body = table[table.index("gAbilityDefinitions[] = {"):]
    blocks = re.split(r"\n    // [^\n]*\n", body)[1:]
    pp, battle = [], []
    for b in blocks:
        m = re.search(r"\.ppCost = (\d+)", b)
        pp.append(int(m.group(1)) if m else 0)
        battle.append("USABLE_IN_BATTLE" in b)
    return pp, battle



# --------------------------------------------------------------- editorial: regions
# Story regions in play order, as sets of zone ids. This is the only hand-made part: the
# zone numbers follow the game's own order and the comments in encounter_zones.c name the
# places. "boss" lists (scene file stem) of the scenes whose scripted battle caps the region
# (checked against the scripted-battle table below).
REGIONS = [
    ("Sol Sanctum and Vale", [1, 2, 3, 4, 5, 6, 7, 8, 12],
     ["vale_kradens_cottage", "vale_prologue", "vale_plaza"]),
    ("Goma Cave", [9, 10, 11], ["goma_cave_pillar"]),
    ("Kolima Forest", [13, 14, 15, 16, 17, 18, 19], ["kolima"]),
    ("Tret Tree", [20, 21, 22, 23, 24], ["tree_rooms", "tret_tree_branch"]),
    ("Bilibin Cave and the snowfield", [25, 26, 27, 28, 29, 30], ["bilibin"]),
    ("Mercury Lighthouse", [31, 32, 33, 34, 35, 36],
     ["mercury_lighthouse", "mercury_lighthouse_entrance", "mercury_lighthouse_aerie"]),
    ("Fuchin Falls Cave", [37, 38, 39, 40, 41], ["imil_fuchin_falls", "xian"]),
    ("Mogall Forest", [42, 43, 44], ["mogall_forest"]),
    ("Altin Peak and Lamakan Desert", [45, 46, 47, 48, 49, 50, 51, 52, 53],
     ["altin_peak", "lamakan_desert"]),
    ("Vale Cave and Vault Cave", [54, 55, 56, 57, 58, 59, 60, 61],
     ["vale_cave", "vault", "vault_revisit", "log_rooms_a"]),
    ("Tolbi ship", [62], ["ship_rooms", "tolbi_ship_deck", "kalay_tolbi_docks", "tolbi", "kalay"]),
    ("Crossbone Isle", [63, 84], ["crossbone_isle", "crossbone_isle_keys"]),
    ("Altmiller Cave", [64, 65, 66, 67, 68, 69, 70, 71], ["altmiller_cave"]),
    ("Colosso", [72], ["colosseum_azart_match", "colosseum_satrage_match", "colosseum_navampa_match"]),
    ("Gondowan Cave and Lunpa Fortress", [73, 74, 75, 76, 77, 78, 79], ["lunpa_fortress", "lalivero"]),
    ("Suhalla Desert", [80, 81, 82, 83], ["suhalla_desert", "world_map:WorldMap_DouseMapStorm"]),
    ("Suhalla Gate and Gateway Cave", [85, 86, 87, 88], ["suhalla_gate"]),
    ("Venus Lighthouse: ground floor", [89, 90], []),
    ("Babi Lighthouse and Tunnel Ruins", [91, 92, 93], ["babi_lighthouse"]),
    ("Venus Lighthouse: upper floors and aerie", [94, 95, 96, 97, 98], ["venus_lighthouse_aerie"]),
]


def main():
    en = parse_enemies()
    fo = parse_formations()
    zo = parse_zones()
    rules = parse_rules()
    wm = parse_worldmap_rules()
    battles, djinn_scenes = scan_scenes()
    djn = parse_djinn()
    djids = parse_djinn_ids()
    zc = parse_zone_consts()
    small = parse_small()
    assert len(fo) == 380, "formations: %d" % len(fo)
    assert len(zo) == 104, "zones: %d" % len(zo)

    def ename(i):
        return en[i]["name"] if 0 <= i < len(en) else "?%d" % i

    def elvl(i):
        return en[i]["level"] if 0 <= i < len(en) else 0

    def form_slots(fid):
        """sprite slots at the minimum counts: a small enemy takes 1 of the 6, any other 2"""
        f = fo[fid]
        return sum(mn * (1 if small[m + 8] else 2) for m, mn in zip(f["members"], f["mn"]) if mn)

    def form_text(fid):
        f = fo[fid]
        parts = []
        for m, lo, hi in zip(f["members"], f["mn"], f["mx"]):
            if hi == 0:
                continue
            cnt = str(lo) if lo == hi else "%d-%d" % (lo, hi)
            parts.append("%s x%s (L%d, #%d%s)" % (ename(m), cnt, elvl(m), m, "" if small[m + 8] else ", large"))
        return (", ".join(parts) if parts else "(empty)") + " [%d slots]" % form_slots(fid)

    def form_levels(fid):
        f = fo[fid]
        ls = [elvl(m) for m, hi in zip(f["members"], f["mx"]) if hi]
        return (min(ls), max(ls)) if ls else (0, 0)

    L = []
    w = L.append
    w("# Cup candidates (generated)")
    w("")
    w("Generated by `scripts/cup-candidates.py` from the source tables of the alchemy working copy (branch `arena`).")
    w("Do not edit by hand; re-run the script. Enemy levels and stats are OUR enemy table's")
    w("(the Reloaded retune). `#n` is the enemy-table row, the number a `Formation.memberIds`")
    w("entry (and a ladder `ARENA_TEAM`) uses. The zone number is the row of `gEncounterZones`;")
    w("the formation number is the row of `gFormations`. The zone's own `level` is the party")
    w("level the stock game made it for; the mobs' levels are the enemy table's.")
    w("")
    w("Evidence of area data: `encounter_zones.c` comments name each zone's place, `encounter_rules.s`")
    w("maps scene (and entrance) to zone, `world_map_encounter_rules.c` maps world-map region and")
    w("terrain to zone, and `Field_RequestBattleFromEncounterTable(zone, slot)` calls in `src/scene`")
    w("start the story's scripted battles (bosses). The grouping into regions below is the only")
    w("editorial layer (`REGIONS` in the script).")
    w("")

    # world map table
    w("## World map encounter regions")
    w("")
    w("| Region | Terrain behaviour | Zone | Zone level | Zone comment |")
    w("|---|---|---|---|---|")
    for reg, beh, flag, zone in wm:
        w("| %d | %d | %d | %d | %s |" % (reg, beh, zone, zo[zone]["level"], zo[zone]["comment"]))
    w("")

    # Regions
    w("## Regions, in story order")
    w("")
    w("Mob level = the enemy table level of the formation's members; a formation's range is shown")
    w("as `lo-hi`. Weights are the zone's chance weights for that formation.")
    w("")
    uses_all = defaultdict(set)
    for fn in sorted(os.listdir(os.path.join(GAME, "src/scene"))):
        if fn.endswith(".c"):
            for m in re.finditer(r"\b(DJINNI_[A-Z0-9_]+)\b", read("src/scene/" + fn)):
                uses_all[m.group(1)].add(fn[:-2])
    region_zone = {}
    for ri, (rname, zs, rscenes) in enumerate(REGIONS):
        for z in zs:
            region_zone[z] = ri
    for ri, (rname, zs, rscenes) in enumerate(REGIONS):
        rz = [z for z in zs if zo[z]["rate"]]
        zl = [zo[z]["level"] for z in rz]
        w("### %d. %s" % (ri + 1, rname))
        w("")
        w("Zones %s; random-battle zone levels %s." % (", ".join(map(str, zs)),
                                                        "%d-%d" % (min(zl), max(zl)) if zl else "n/a"))
        w("")
        w("| Zone | Place (source comment) | Rate | Zone lvl | Scenes (encounter_rules.s) |")
        w("|---|---|---|---|---|")
        for z in zs:
            zz = zo[z]
            sc = []
            for s, e in rules.get(z, []):
                if s not in sc:
                    sc.append(s)
            w("| %d | %s | %d | %d | %s |" % (z, zz["comment"], zz["rate"], zz["level"], ", ".join(sc)))
        w("")
        # formations of the random zones, summed weights; scripted zones listed apart
        fw = OrderedDict()
        for z in rz:
            zz = zo[z]
            for fid, wt in zip(zz["forms"], zz["weights"]):
                fw[fid] = fw.get(fid, 0) + wt
        if fw:
            w("Random formations (weights summed over the region's zones):")
            w("")
            w("| Formation | Members (enemy lvl, row) | Weight |")
            w("|---|---|---|")
            for fid in sorted(fw, key=lambda f: (form_levels(f)[1], f)):
                w("| f%d | %s | %d |" % (fid, form_text(fid), fw[fid]))
            w("")
        # scripted battles and Djinn whose scene belongs to this region
        def in_region(scene, fnc):
            return scene in rscenes or ("%s:%s" % (scene, fnc)) in rscenes
        seen_b = []
        for scene, fnc, zone, slot in battles:
            if not in_region(scene, fnc):
                continue
            try:
                zid = int(zone) if zone.isdigit() else zc[zone]
                sl = int(slot.split()[0].rstrip(","))
                fid = zo[zid]["forms"][sl]
            except Exception:
                continue
            ent = "%s (%s): f%d %s" % (fnc, scene, fid, form_text(fid))
            if ent not in seen_b:
                seen_b.append(ent)
        if not seen_b:
            # computed slots (the Colosso matches): list every slot of the region's event zones
            for z in zs:
                if zo[z]["rate"] == 0 and z != 0 and zo[z]["forms"]:
                    for si, fid in enumerate(zo[z]["forms"]):
                        seen_b.append("zone %d slot %d (%s): f%d %s" % (z, si, zo[z]["comment"], fid, form_text(fid)))
        if seen_b:
            w("Scripted battles (bosses and set pieces) in this region's scenes:")
            w("")
            for ent in seen_b:
                w("- " + ent)
            w("")
        dj = sorted({d for sc, d in djinn_scenes if sc in rscenes} |
                    {d for d, scs in uses_all.items() if any(sc in rscenes for sc in scs) and d in djids},
                    key=lambda d: djids[d])
        if dj:
            w("Djinn in this region's scenes: " + ", ".join(
                "%s (%s)" % (djn[djids[d]], ["Venus", "Mercury", "Mars", "Jupiter"][djids[d] // 20]) for d in dj) + ".")
            w("")
        eset = {}
        for fid in fw:
            for m, hi in zip(fo[fid]["members"], fo[fid]["mx"]):
                if hi:
                    eset[m] = 1
        if eset:
            w("Mobs by enemy level: " + ", ".join(
                "%s L%d (#%d)" % (ename(m), elvl(m), m) for m in sorted(eset, key=lambda x: (elvl(x), x))))
            w("")

    # boss battles
    w("## Scripted battles (bosses and set pieces)")
    w("")
    w("From `Field_RequestBattleFromEncounterTable(zone, slot)` calls in `src/scene`; the slot")
    w("picks `gEncounterZones[zone].enemies[slot]`, a formation. Event zones: " +
      ", ".join("%s=%d" % kv for kv in sorted(zc.items(), key=lambda kv: kv[1])) + ".")
    w("")
    w("| Scene file | Function | Zone | Slot | Formation | Members (enemy lvl) |")
    w("|---|---|---|---|---|---|")
    for scene, fnc, zone, slot in battles:
        try:
            zid = int(zone) if zone.isdigit() else zc[zone]
            sl = int(slot.split()[0].rstrip(",")) if re.match(r"^\d+$", slot.split()[0].rstrip(",")) else None
        except Exception:
            zid, sl = None, None
        if zid is not None and sl is not None and sl < len(zo[zid]["forms"]):
            fid = zo[zid]["forms"][sl]
            w("| %s | %s | %s (%d) | %s | f%d | %s |" % (scene, fnc, zone, zid, slot, fid, form_text(fid)))
        else:
            w("| %s | %s | %s | `%s` | (computed: see source) | |" % (scene, fnc, zone, slot))
    w("")
    w("Zones whose slots all hold scripted battles, expanded (every slot, for the computed calls):")
    w("")
    for name, zid in sorted(zc.items(), key=lambda kv: kv[1]):
        if name in ("ENCOUNTER_ZONE_NONE",) or "DJINN" in name or "MIMIC" in name:
            continue
        w("- **%s (%d)** %s" % (name, zid, zo[zid]["comment"]))
        for si, fid in enumerate(zo[zid]["forms"]):
            w("  - slot %d: f%d: %s" % (si, fid, form_text(fid)))
    w("")

    # Djinn battle formations
    w("## Djinn battles and Djinn in scenes")
    w("")
    w("Djinn are caught by winning their battle: `Field_RequestDjinnBattle(actor, DJINNI_X)` in a")
    w("scene. The scene file is where the Djinni is; the enemy is a Djinni row of the enemy table")
    w("(zones 100 to 103). Scenes that name a Djinni (this lists only those that fight):")
    w("")
    # gEncounter_AreaEntryTable: 160 u16, {zone, slot} per Djinni number (element * 20 + index)
    wm_text = read("src/field/world_map_encounter_rules.c")
    ae = wm_text[wm_text.index("gEncounter_AreaEntryTable[160] = {"):]
    ae = [int(x) for x in re.findall(r"\d+", ae.split("{", 1)[1].split("}", 1)[0])]
    w("| Djinni | Table index | Scene file | Battle (zone, slot) | Formation: enemy (level) |")
    w("|---|---|---|---|---|")
    for scene, d in sorted(djinn_scenes, key=lambda x: djids.get(x[1], 0)):
        idx = djids.get(d, -1)
        if idx < 0:
            continue
        zid, slot = ae[idx * 2], ae[idx * 2 + 1]
        fid = zo[zid]["forms"][slot % len(zo[zid]["forms"])]
        w("| %s | %d | %s | %d, %d | f%d: %s |" % (djn[idx], idx, scene, zid, slot, fid, form_text(fid)))
    w("")
    # all DJINNI_ uses in scene files (to catch gifts)
    base = os.path.join(GAME, "src/scene")
    uses = defaultdict(set)
    for fn in sorted(os.listdir(base)):
        if fn.endswith(".c"):
            t = read("src/scene/" + fn)
            for m in re.finditer(r"\b(DJINNI_[A-Z0-9_]+)\b", t):
                uses[m.group(1)].add(fn[:-2])
    w("Every scene file that mentions a Djinni constant (a fight, a gift or a flag):")
    w("")
    w("| Djinni | Index | Scene files |")
    w("|---|---|---|")
    for d in sorted(uses, key=lambda x: djids.get(x, 999)):
        idx = djids.get(d, -1)
        w("| %s | %d | %s |" % (djn[idx] if 0 <= idx < len(djn) else d, idx, ", ".join(sorted(uses[d]))))
    w("")

    # today's ladders, with their sprite slots
    lad = read("src/battle/battle/arena_ladder.c")
    w("## Today's ladders (`arena_ladder.c`), with sprite slots")
    w("")
    w("Six sprite slots a team: a small enemy takes 1, any other 2 (`BattleFormation_BuildEnemyList`).")
    w("")
    for title, key, nxt in (("Monster Gauntlet", "gArenaLadder[", "gArenaBossRush["),
                            ("Boss Rush", "gArenaBossRush[", "// clang-format on")):
        sect = lad[lad.index(key):]
        sect = sect[:sect.index(nxt)] if nxt in sect else sect
        w("**%s**" % title)
        w("")
        w("| Rung | Target lvl | Members (own lvl) | Slots | Level margin (target - mean own level) |")
        w("|---|---|---|---|---|")
        rung = 0
        for m in re.finditer(r"ARENA_TEAM\((\d+), \.memberIds = \{([^}]*)\}, \.minimumCounts = \{([^}]*)\}", sect):
            tgt = int(m.group(1))
            ids = [int(x) for x in m.group(2).split(",")]
            cnt = [int(x) for x in m.group(3).split(",")]
            ls = [elvl(i) for i in ids]
            sl = sum(c * (1 if small[i + 8] else 2) for i, c in zip(ids, cnt))
            rung += 1
            w("| %d | %d | %s | %d%s | %+d |" % (
                rung, tgt, ", ".join("%s x%d (L%d)" % (ename(i), c, elvl(i)) for i, c in zip(ids, cnt)),
                sl, " **over 6**" if sl > 6 else "", tgt - sum(ls) // len(ls)))
        w("")

    # shops
    items = parse_items()
    stock = parse_stock()
    w("## Shop stock rows (the item shops, in story order)")
    w("")
    w("`sStockTable` in `shop/shop/stock.c`: one row per shop, in the order the story reaches the")
    w("towns. The arena's manager opens rows 16 to 18 (Xian) today (`TRAINING_SHOP_FIRST_ROW`).")
    w("A row's type column: 0 supplies, 1 weapons, 2 armor. Town per `Shop_Run` calls in `src/scene`.")
    w("")
    w("| Row | Town (scene file) | Type | Items (price) | Artifacts |")
    w("|---|---|---|---|---|")
    typ = {0: "supplies", 1: "weapons", 2: "armor"}
    for ri, row in enumerate(stock):
        if ri == 0:
            continue
        town = SHOP_ROWS.get(ri, "")
        its = ["%s (%d)" % (items[i]["name"], items[i]["price"]) for i in row[:24] if i]
        arts = [items[i]["name"] for i in row[24:32] if i]
        w("| %d | %s | %s | %s | %s |" % (ri, town, typ.get(row[32], row[32]), ", ".join(its), ", ".join(arts)))
    w("")

    # Psynergy tiers
    ca = parse_class_abilities()
    an = parse_ability_names()
    pp, battle = parse_ability_pp()
    first_level = {a: min(l for l, c in v) for a, v in ca.items() if a < 519 and battle[a]}
    w("## Psynergy by the level a class first teaches it")
    w("")
    w("Battle abilities taught by any class (`class_table.c`), by the lowest level any class")
    w("teaches them. A class teaches only what its series holds; this is the pool the levels open.")
    w("")
    w("| Levels | New battle abilities | Cumulative | Examples (PP) |")
    w("|---|---|---|---|")
    cum = 0
    for lo, hi in [(1, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 59), (60, 99)]:
        ab = sorted((a for a, l in first_level.items() if lo <= l <= hi), key=lambda a: (first_level[a], a))
        cum += len(ab)
        ex = ", ".join("%s %d" % (an.get(a, "?"), pp[a]) for a in ab[:10])
        w("| %d-%d | %d | %d | %s |" % (lo, hi, len(ab), cum, ex))
    w("")
    top = max(first_level.values())
    w("Highest level at which any class teaches a battle ability: %d." % top)
    w("")

    # scaling check: an enemy moved to a target level by BattleEnemy_AdjustLevel against the
    # party's base stats at that level (closed form, ArenaRules_LevelGain)
    chars = parse_characters()

    def cdiv(a, b):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b >= 0) else -q

    def party_base(char, level):
        out = []
        for g in char:
            v = g[0]
            for lv in range(1, level + 1):
                band = min(lv // 20, 4)
                d = g[band + 1] - g[band]
                span = 20 if lv >= 20 else 19
                v += cdiv(lv * d, span) - cdiv((lv - 1) * d, span)
            out.append(v)
        return out

    def adjust(e, levels):
        def one(base, per, cap):
            v = base + cdiv(levels * per, 10)
            return max(min(v, cap), base * 7 // 10)
        return [one(e["hp"], 97, 9999), one(e["atk"], 123, 999), one(e["dfn"], 33, 999),
                one(e["agi"], 51, 999)]

    w("## Scaling check: an enemy moved to the party's level")
    w("")
    w("`BattleEnemy_AdjustLevel` adds per level: 9.7 HP, 12.3 Attack, 3.3 Defense, 5.1 Agility,")
    w("never below 70 percent of the base value, capped at 9999 HP and 999 for the others. The party's")
    w("base stats are the mean of Isaac, Garet, Ivan and Mia from the closed form of the level-up rule")
    w("(before Djinn, class and gear). The ratio is enemy / party: the same ratio across levels")
    w("means margin-scaling keeps the fight's shape; 999 means the cap is reached.")
    w("")
    w("| Enemy (own level) | Party level | Enemy HP / Atk / Def / Agi | Party base HP / Atk / Def / Agi | Ratio HP, Atk, Def, Agi |")
    w("|---|---|---|---|---|")
    samples = [91, 80, 121, 141]  # Wild Gryphon, Thunder Lizard, Lizard King, Deadbeard
    for row in samples:
        e = en[row]
        for lv in (10, 20, 30, 40, 50, 60, 70, 80, 99):
            es = adjust(e, lv - e["level"])
            pb = [party_base(c, lv) for c in chars[:4]]
            pm = [sum(p[i] for p in pb) // 4 for i in (0, 2, 3, 4)]
            ratio = ", ".join("%.1f" % (a / b) for a, b in zip(es, pm))
            w("| %s (L%d) | %d | %s | %s | %s |" % (e["name"], e["level"], lv,
                                                    " / ".join(str(x) for x in es),
                                                    " / ".join(str(x) for x in pm), ratio))
    w("")

    # early-cup check: region mobs and bosses moved to the first brackets' party levels
    w("## Early cups: mobs and bosses moved to party level 10 and 20")
    w("")
    w("The party level-10 start of `CUPS.md`, with enemy rows from the early regions moved to the")
    w("cup level by `BattleEnemy_AdjustLevel` (never below 70 percent of base). Party figure is the")
    w("mean base stat of the four characters (no Djinn, class or gear, which add to it).")
    w("")
    w("| Enemy (own level) | Cup level | Enemy HP / Atk / Def / Agi | Party base HP / Atk / Def / Agi | Ratio HP, Atk, Def, Agi |")
    w("|---|---|---|---|---|")
    for row in (1, 4, 10, 18, 24, 39, 45, 51, 54, 119, 139, 115):
        e = en[row]
        for lv in (10, 20):
            es = adjust(e, lv - e["level"])
            pb = [party_base(c, lv) for c in chars[:4]]
            pm = [sum(p[i] for p in pb) // 4 for i in (0, 2, 3, 4)]
            ratio = ", ".join("%.1f" % (a / b) for a, b in zip(es, pm))
            w("| %s (L%d) | %d | %s | %s | %s |" % (e["name"], e["level"], lv,
                                                    " / ".join(str(x) for x in es),
                                                    " / ".join(str(x) for x in pm), ratio))
    w("")

    # party base stats per character at the cup levels (what ArenaCup_SetLevel would write)
    w("## Party base stats by level (the closed form, before Djinn, class and gear)")
    w("")
    w("What `ArenaCup_SetLevel(level)` would write into `baseHp` ... `baseLuck`, from the growth")
    w("curves in `character_table.c` by the rule of `ArenaRules_LevelGain`. Character order is the")
    w("table's (Isaac, Garet, Ivan, Mia, unit ids 0 to 3).")
    w("")
    w("| Level | Character | HP | PP | Atk | Def | Agi | Luck |")
    w("|---|---|---|---|---|---|---|---|")
    for lv in (10, 20, 30, 40, 50, 99):
        for name, c in zip(("Isaac", "Garet", "Ivan", "Mia"), chars[:4]):
            w("| %d | %s | %s |" % (lv, name, " | ".join(str(x) for x in party_base(c, lv))))
    w("")

    # enemy table by level
    w("## The enemy table by level")
    w("")
    w("All %d rows, sorted by level, for hand-built teams and side cups. HP/ATK/DEF/AGI are the" % len(en))
    w("base values the battle then adjusts by the level margin (`BattleEnemy_AdjustLevel`).")
    w("")
    w("| Row | Name | Level | HP | Atk | Def | Agi | Luck | Exp | Coins |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for i in sorted(range(len(en)), key=lambda i: (en[i]["level"], i)):
        e = en[i]
        w("| %d | %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            i, e["name"], e["level"], e["hp"], e["atk"], e["dfn"], e["agi"], e["luck"], e["exp"], e["coins"]))
    w("")

    text = "\n".join(L) + "\n"
    if OUT:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Port the data tables of the Golden Sun Reloaded TBS patch into our C sources.

Usage:
  port-reloaded-tables.py --ips PATCH.ips --rom STOCK.gba --elf STOCK.elf \
      [--src ~/alchemy/games/tbs] [--check] [--report FILE] [TABLE ...]

TABLE is one of: abilities classes items enemies presets characters djinn (default: all).

How it works. The IPS patch is applied in memory to an unmodified build of the game (the
"stock" ROM, never the owner's dump, built from upstream's source in ~/alchemy-stock).
Each table is split into records using the symbol's size in the stock ELF and the record
layout below (read from games/tbs/include/game/*.h and battle/battle_unit.h). The record
before and after the patch is decoded into fields, and where a field differs the matching
row of our C table (games/tbs/src/game/*_table.c) is edited: the row's comment and layout
stay, unchanged fields are kept as written, a changed field is written again (named
constants where our headers have the enum, a number otherwise), and a field that is now 0
is left out, as the tables do everywhere.

--check does not write; it renders every row of the stock table and compares it with the
source (the converter's formatter against the existing text) and lists what differs, then
reports which rows would change. Run it before the real thing.

The result no longer depends on the patch: the numbers are in the C source. The patch's
authors are credited in the table files' headers and in docs/RELOADED.md (Golden Sun
Reloaded, forum.goldensunhacking.net topic 2779).

Bytes of a record that no named field covers (reserved and padding bytes) are compared
too; if the patch changes one, a warning is printed (nothing is written for it).
"""
import argparse
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alchemy_dir  # noqa: E402


# ---------------------------------------------------------------------------
# IPS, symbols

def apply_ips(rom, path):
    data = open(path, "rb").read()
    out = bytearray(rom)
    i = 5
    while data[i:i + 3] != b"EOF":
        off = int.from_bytes(data[i:i + 3], "big")
        size = int.from_bytes(data[i + 3:i + 5], "big")
        i += 5
        if size == 0:
            size = int.from_bytes(data[i:i + 2], "big")
            payload = data[i + 2:i + 3] * size
            i += 3
        else:
            payload = data[i:i + size]
            i += size
        if off + size > len(out):
            out.extend(b"\xff" * (off + size - len(out)))
        out[off:off + size] = payload
    return bytes(out)


def symbols(elf):
    out = subprocess.run(["arm-none-eabi-nm", "-S", elf], capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) == 4:
            table[p[3]] = (int(p[0], 16), int(p[1], 16))
    return table


# ---------------------------------------------------------------------------
# Names from our headers

def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def parse_enums(path):
    """All `enum Name { A = x, B, ... }` of a header: {EnumName: {CONST: value}}."""
    text = strip_comments(open(path, encoding="utf-8").read())
    result = {}
    for m in re.finditer(r"enum\s+(\w+)\s*\{(.*?)\}\s*;", text, flags=re.S):
        values = {}
        nxt = 0
        for item in m.group(2).split(","):
            item = item.strip()
            if not item:
                continue
            if "=" in item:
                name, expr = [s.strip() for s in item.split("=", 1)]
                try:
                    nxt = int(eval(expr, {}, dict(values)))
                except Exception:
                    continue
            else:
                name = item
            values[name] = nxt
            nxt += 1
        result[m.group(1)] = values
    return result


def parse_defines(path, prefix):
    text = strip_comments(open(path, encoding="utf-8").read())
    out = {}
    for m in re.finditer(r"#define\s+(%s\w*)\s+(\w+)" % prefix, text):
        try:
            out[m.group(1)] = int(m.group(2), 0)
        except ValueError:
            pass
    return out


def invert(d):
    inv = {}
    for k, v in d.items():
        inv.setdefault(v, k)
    return inv


class Names:
    def __init__(self, inc):
        ab = parse_enums(os.path.join(inc, "battle", "battle_unit.h"))
        item = parse_enums(os.path.join(inc, "game", "item.h"))
        self.effect = invert(ab["AbilityEffect"])
        # Ids whose handler the Reloaded rules alias (ARENA_RULES_EFFECT_IDS): these
        # take the names arena_config.h gives them.
        self.effect.update(ARENA_EFFECT_NAMES)
        self.target = invert(ab["AbilityTarget"])
        self.formula = invert(next(v for k, v in ab.items() if "ABILITY_FORMULA_DAMAGE" in v))
        self.ability_id = invert(parse_enums(os.path.join(inc, "ability_ids.h"))["AbilityId"])
        self.item_id = invert(parse_enums(os.path.join(inc, "item_ids.h"))["ItemId"])
        self.item_type = invert(item["ItemType"])
        self.item_flag = item["ItemFlags"]
        self.equip_kind = invert(item["EquipEffectKind"])
        self.use_type = invert(parse_defines(os.path.join(inc, "game", "item.h"), "ITEM_USE_"))
        self.range_all = 255


# Effect ids the Reloaded engine rules reuse (see arena_config.h, "Effect ids").
ARENA_EFFECT_NAMES = {
    36: "ARENA_EFFECT_DULL_2",
    37: "ARENA_EFFECT_IMPAIR_2",
    38: "ARENA_EFFECT_WEAKEN_2",
    39: "ARENA_EFFECT_TAINT",
    40: "ARENA_EFFECT_POISON",
    41: "ARENA_EFFECT_PARALYZE_2",
    43: "ARENA_EFFECT_HAUNT_2",
    54: "ARENA_EFFECT_CONDEMN_2",
}

ELEMENT = {0: "ELEMENT_VENUS", 1: "ELEMENT_MERCURY", 2: "ELEMENT_MARS", 3: "ELEMENT_JUPITER", 4: "ELEMENT_NONE"}
CHARACTER = ["ISAAC", "GARET", "IVAN", "MIA", "FELIX", "JENNA", "SHEBA", "PIERS"]


# ---------------------------------------------------------------------------
# Value formatting. Each returns the text of a field's value.

def num(N, v):
    return str(v)


def f_hex(N, v):
    return "0x%x" % v


def f_element(N, v):
    return ELEMENT.get(v, str(v))


def f_target(N, v):
    return N.target.get(v, str(v))


def f_ability_flags(N, v):
    parts = []
    if v & 0x40:
        parts.append("ABILITY_USABLE_IN_FIELD")
    if v & 0x80:
        parts.append("ABILITY_USABLE_IN_BATTLE")
    if v & 0x30:
        parts.append("%#x" % (v & 0x30))
    low = v & 0x0f
    if low:
        parts.append(N.formula.get(low, str(low)))
    return " | ".join(parts) if parts else "0"


def f_effect(N, v):
    return N.effect.get(v, str(v))


def f_range(N, v):
    return "ABILITY_RANGE_ALL" if v == 255 else str(v)


def f_item_type(N, v):
    return N.item_type.get(v, str(v))


def f_item_flags(N, v):
    parts = [name for name, bit in sorted(N.item_flag.items(), key=lambda kv: kv[1]) if v & bit]
    rest = v & ~sum(N.item_flag.values())
    if rest:
        parts.append("%#x" % rest)
    return " | ".join(parts) if parts else "0"


def f_equip_mask(N, v):
    if v == 0xff:
        return "EQUIP_ALL_CHARACTERS"
    parts = ["EQUIP_CHARACTER(%s)" % CHARACTER[i] for i in range(8) if v & (1 << i)]
    rest = v & ~0xff
    if rest:
        parts.append("%#x" % rest)
    return " | ".join(parts) if parts else "0"


def f_use_type(N, v):
    return N.use_type.get(v, str(v))


def f_item_ref(N, v):
    return N.item_id.get(v, str(v))


def f_ability_ref(N, v):
    return N.ability_id.get(v, str(v))


def f_strategy_t(N, v):
    return {0: "TARGET_STRATEGY_MOST_HP", 1: "TARGET_STRATEGY_MOST_MAX_HP", 2: "TARGET_STRATEGY_RANDOM"}.get(v, str(v))


def f_strategy_a(N, v):
    names = ["ACTION_STRATEGY_EVEN", "ACTION_STRATEGY_FALLING", "ACTION_STRATEGY_FIRST_FAVOURED",
             "ACTION_STRATEGY_RANDOM_START", "ACTION_STRATEGY_IN_ORDER", "ACTION_STRATEGY_NEXT_PICK",
             "ACTION_STRATEGY_SAME"]
    return names[v] if 0 <= v < len(names) else str(v)


# ---------------------------------------------------------------------------
# Table specs. A field is (name, kind, offset, struct format, count, formatter).
#   scalar: one value; array: `count` values, trailing zeros left out;
#   full: array written whole; special kinds are handled in render().

def S(name, off, fmt, fn=num, always=False):
    return dict(name=name, kind="scalar", off=off, fmt=fmt, fn=fn, always=always)


def A(name, off, fmt, count, fn=num, trim=True):
    return dict(name=name, kind="array", off=off, fmt=fmt, count=count, fn=fn, trim=trim)


TABLES = {}

TABLES["abilities"] = dict(
    symbol="gAbilityDefinitions", rec=16, file="ability_table.c", decl="gAbilityDefinitions",
    fields=[S("targetMode", 0, "B", f_target, True), S("flags", 1, "B", f_ability_flags),
            S("element", 2, "B", f_element, True), S("effect", 3, "B", f_effect), S("icon", 4, "B"),
            S("range", 8, "B", f_range), S("ppCost", 9, "B"), S("power", 10, "H"),
            S("fieldPsynergy", 12, "B")],
    reserved=[(5, 8), (13, 16)])

TABLES["classes"] = dict(
    symbol="gClass_DefinitionTable", rec=84, file="class_table.c", decl="gClass_DefinitionTable",
    fields=[S("series", 0, "i"), A("required", 4, "B", 4),
            S("hp", 8, "B"), S("pp", 9, "B"), S("atk", 10, "B"), S("agi", 12, "B"), S("def", 11, "B"),
            S("luck", 13, "B"),
            dict(name="abilities", kind="classabilities", off=16, count=16),
            A("weakEffects", 80, "B", 3, f_effect), S("ward", 83, "B")],
    order=["series", "required", "hp", "pp", "atk", "def", "agi", "luck", "abilities", "weakEffects", "ward"],
    reserved=[(14, 16)])

TABLES["items"] = dict(
    symbol="gItem_DefinitionTable", rec=44, file="item_table.c", decl="gItem_DefinitionTable",
    fields=[S("price", 0, "h"), S("type", 2, "B", f_item_type), S("flags", 3, "B", f_item_flags),
            S("equipMask", 4, "H", f_equip_mask), S("icon", 6, "H"), S("primaryBonus", 8, "h"),
            S("secondaryBonus", 10, "b"), S("unleashChance", 11, "B"), S("useType", 12, "B", f_use_type),
            S("unleashAbility", 14, "H", f_ability_ref), S("element", 20, "i", f_element),
            dict(name="effects", kind="effects", off=24, count=4), S("abilityId", 40, "H", f_ability_ref)],
    order=["price", "type", "flags", "equipMask", "icon", "primaryBonus", "secondaryBonus",
           "unleashChance", "useType", "unleashAbility", "element", "effects", "abilityId"],
    reserved=[(13, 14), (16, 20), (42, 44)])

TABLES["enemies"] = dict(
    symbol="gEnemy_Definitions", rec=84, file="enemy_table.c", decl="gEnemy_Definitions",
    fields=[S("level", 15, "B"), S("hp", 16, "H"), S("pp", 18, "H"), S("atk", 20, "H"), S("def", 22, "H"),
            S("agi", 24, "H"), S("luck", 26, "B"), S("actionCount", 27, "B"), S("hpRegen", 28, "B"),
            S("ppRegen", 29, "B"), A("items", 40, "H", 4, f_item_ref), A("counts", 48, "B", 4),
            S("elementPreset", 52, "B"), S("targetStrategy", 53, "b", f_strategy_t),
            S("actionStrategy", 54, "b", f_strategy_a), S("itemActions", 55, "B", f_hex),
            A("abilities", 56, "H", 8, f_ability_ref), A("weakEffects", 72, "B", 3, f_effect),
            S("coins", 76, "H"), S("item", 78, "h", f_item_ref), S("itemChance", 80, "h"),
            S("experience", 82, "H")],
    order=["name", "level", "hp", "pp", "atk", "def", "agi", "luck", "actionCount", "hpRegen", "ppRegen",
           "items", "counts", "elementPreset", "targetStrategy", "actionStrategy", "itemActions",
           "abilities", "weakEffects", "coins", "item", "itemChance", "experience"],
    reserved=[(0, 15), (30, 40)])

TABLES["presets"] = dict(
    symbol="gEnemy_ElementPresetTable", rec=24, file="element_table.c", decl="gEnemy_ElementPresetTable",
    fields=[S("first", 0, "i", f_element, True), A("digits", 4, "B", 4, num, trim=False),
            dict(name="values", kind="presetvalues", off=8, count=4)],
    reserved=[])

TABLES["characters"] = dict(
    symbol="gCharacter_DefinitionTable", rec=180, file="character_table.c", decl="gCharacter_DefinitionTable",
    fields=[A("hp", 0x50, "h", 6, num, trim=False), A("pp", 0x5c, "h", 6, num, trim=False),
            A("atk", 0x68, "H", 6, num, trim=False), A("def", 0x74, "H", 6, num, trim=False),
            A("agi", 0x80, "H", 6, num, trim=False), A("luck", 0x8c, "B", 6, num, trim=False),
            A("elementBonus", 0x92, "B", 4, num, trim=False), S("startingLevel", 0x96, "B"),
            A("items", 0x98, "H", 13, f_item_ref)],
    reserved=[(0, 0x50), (0x97, 0x98), (0xb2, 0xb4)])

TABLES["djinn"] = dict(
    symbol="gDjinn_DefinitionTable", rec=12, file="djinn_table.c", decl="gDjinn_DefinitionTable",
    fields=[S("abilityId", 0, "H", f_ability_ref, True), S("hp", 4, "b"), S("pp", 5, "b"), S("atk", 6, "b"),
            S("def", 7, "b"), S("agi", 8, "b"), S("luck", 9, "b")],
    order=["abilityId", "hp", "pp", "atk", "def", "agi", "luck"],
    reserved=[(2, 4), (10, 12)])


def decode(spec, rec):
    """A record's fields as {name: value}; arrays are lists, compound fields lists of tuples."""
    out = {}
    for f in spec["fields"]:
        k = f["kind"]
        if k == "scalar":
            out[f["name"]] = struct.unpack_from("<" + f["fmt"], rec, f["off"])[0]
        elif k == "array":
            w = struct.calcsize("<" + f["fmt"])
            out[f["name"]] = [struct.unpack_from("<" + f["fmt"], rec, f["off"] + i * w)[0] for i in range(f["count"])]
        elif k == "classabilities":
            out["abilities"] = [(rec[16 + 4 * i], rec[17 + 4 * i]) for i in range(16)]
            if any(rec[18 + 4 * i] or rec[19 + 4 * i] for i in range(16)):
                out["_abilitypad"] = 1
        elif k == "effects":
            out["effects"] = [(rec[24 + 4 * i], struct.unpack_from("<b", rec, 25 + 4 * i)[0]) for i in range(4)]
            out["_effectpad"] = bytes(rec[26 + 4 * i] for i in range(4)) + bytes(rec[27 + 4 * i] for i in range(4))
        elif k == "presetvalues":
            vals = [struct.unpack_from("<I", rec, 8 + 4 * i)[0] for i in range(4)]
            out["values"] = [(v & 0xffff, v >> 16) for v in vals]
    return out


def order_of(spec):
    return spec.get("order") or [f["name"] for f in spec["fields"] if f["kind"] != "reserved"]


def field_by_name(spec, name):
    for f in spec["fields"]:
        if f["name"] == name:
            return f
    return None


# ---------------------------------------------------------------------------
# Rendering a field to source lines (indent 8; continuation 12)

IND = " " * 8
IND2 = " " * 12


def trim_zeros(vals):
    v = list(vals)
    while v and not v[-1]:
        v.pop()
    return v


def effect_text(N, e):
    kind = N.equip_kind.get(e[0], str(e[0]))
    if e[1] == 0:
        return "{.kind = %s}" % kind
    return "{.kind = %s, .amount = %d}" % (kind, e[1])


def render(N, spec, name, value):
    """Source lines for `.name = value,` or None when the field is left out."""
    f = field_by_name(spec, name)
    k = f["kind"]
    if k == "scalar":
        if value == 0 and not f["always"]:
            return None
        return [IND + ".%s = %s," % (name, f["fn"](N, value))]
    if k == "array":
        v = trim_zeros(value) if f["trim"] else list(value)
        if not v or (not f["trim"] and not any(v) and name != "digits"):
            return None
        return [IND + ".%s = {%s}," % (name, ", ".join(f["fn"](N, x) for x in v))]
    if k == "classabilities":
        v = list(value)
        while v and v[-1] == (0, 0):
            v.pop()
        if not v:
            return None
        lines = [IND + ".abilities = {"]
        for a, lvl in v:
            lines.append(IND2 + ("{0}," if (a, lvl) == (0, 0) else "{.ability = %d, .level = %d}," % (a, lvl)))
        lines.append(IND + "},")
        return lines
    if k == "effects":
        v = list(value)
        while v and v[-1] == (0, 0):
            v.pop()
        if not v:
            return None
        items = ["{0}" if e == (0, 0) else effect_text(N, e)
                 for e in v]
        if len(items) == 1:
            return [IND + ".effects = {%s}," % items[0]]
        return [IND + ".effects = {"] + [IND2 + i + "," for i in items] + [IND + "},"]
    if k == "presetvalues":
        return [IND + ".values = {"] + [IND2 + "PRESET_STATS(%d, %d)," % (p, r) for p, r in value] + [IND + "},"]
    raise SystemExit("no renderer for " + k)


# ---------------------------------------------------------------------------
# Source rows

class Row:
    def __init__(self, start, end, comment_line):
        self.start = start            # index of the line `    {...`
        self.end = end                # index of the closing line (inclusive)
        self.comment_line = comment_line
        self.chunks = []              # [(fieldname, [lines])]


FIELD_RE = re.compile(r"^        \.(\w+)\s*=")


def parse_rows(lines, decl):
    # find the declaration
    d = next(i for i, l in enumerate(lines) if decl in l and l.rstrip().endswith("{") and "=" in l)
    rows = []
    i = d + 1
    while not lines[i].startswith("};"):
        l = lines[i]
        if l.startswith("    {"):
            if l.rstrip().endswith("},"):
                row = Row(i, i, None)
                inner = l.strip()[1:-2].strip()
                # a one-line row such as `{}`, `{0}`: no fields
                if inner not in ("", "0"):
                    raise SystemExit("unhandled one-line row: " + l)
            else:
                j = i + 1
                while lines[j] != "    },":
                    j += 1
                row = Row(i, j, None)
                cur = None
                for k in range(i + 1, j):
                    m = FIELD_RE.match(lines[k])
                    if m:
                        cur = (m.group(1), [lines[k]])
                        row.chunks.append(cur)
                    else:
                        cur[1].append(lines[k])
            if i > 0 and lines[i - 1].startswith("    //"):
                row.comment_line = i - 1
            rows.append(row)
            i = row.end + 1
        else:
            i += 1
    return rows


def rebuild_row(N, spec, row, old, new, lines_out):
    """Lines of the row after the change: unchanged chunks kept, changed ones written again."""
    order = order_of(spec)
    chunks = dict((n, ls) for n, ls in row.chunks)
    unknown = [n for n in chunks if n not in order]
    body = []
    for name in order:
        if name not in new and name != "name":
            continue
        if name == "name":
            if name in chunks:
                body.extend(chunks[name])
            continue
        if old.get(name) == new.get(name):
            if name in chunks:
                body.extend(chunks[name])
            continue
        r = render(N, spec, name, new[name])
        if r:
            body.extend(r)
    if unknown:
        raise SystemExit("row has fields the converter does not know: %s" % unknown)
    return ["    {"] + body + ["    },"]


# ---------------------------------------------------------------------------
# gAbilityBattleEffects: one u32 per ability id (the battle animation to play), in
# src/battle/ability_staging.c as `NAME | (variant << EFFECT_VARIANT_SHIFT), // Ability`.

EFFECT_FLAGS = [(0x4000, "EFFECT_BY_ID_RANGE"), (0x8000, "EFFECT_SUMMON"), (0x10000, "EFFECT_ON_DOWNED"),
                (0x20000, "EFFECT_OTHER_SIDE"), (0x40000, "EFFECT_VIEW_ACROSS"), (0x80000, "EFFECT_VIEW_REVERSED")]


def battle_effect_text(ids, v):
    if v == 0:
        return "0"
    parts = []
    ident = v & 0xfff
    parts.append(ids.get(ident, "%d" % ident) if (ident or not (v & ~0xfff)) else "0")
    variant = (v & 0x3000) >> 12
    if variant:
        parts[0] = parts[0] + " | (%d << EFFECT_VARIANT_SHIFT)" % variant
    for bit, name in EFFECT_FLAGS:
        if v & bit:
            parts.append(name)
    rest = v & ~(0xfff | 0x3000 | sum(b for b, _ in EFFECT_FLAGS))
    if rest:
        parts.append("0x%x" % rest)
    return " | ".join(parts) if (ident or variant or len(parts) > 1) else parts[0]


def port_battle_effects(args, syms, rom, new_rom, check):
    inc = os.path.join(args.src, "include")
    ids = invert(parse_enums(os.path.join(inc, "module", "battle_effect", "battle_effect.h"))["BattleEffectId"])
    addr, size = syms["gAbilityBattleEffects"]
    base = addr - 0x08000000
    path = os.path.join(args.src, "src", "battle", "ability_staging.c")
    text = open(path, newline="", encoding="utf-8").read()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    start = next(i for i, l in enumerate(lines) if "gAbilityBattleEffects[] = {" in l)
    entry_lines = []
    i = start + 1
    while not lines[i].startswith("};"):
        if re.match(r"^\s+[^/\s].*, // ", lines[i]):
            entry_lines.append(i)
        i += 1
    n = size // 4
    print("== battleeffects: %d entries in the ROM, %d lines in ability_staging.c" % (n, len(entry_lines)))
    if len(entry_lines) != n:
        print("   COUNT DIFFERS; skipping")
        return
    mism = 0
    changed = []
    for r in range(n):
        a = struct.unpack_from("<I", rom, base + 4 * r)[0]
        b = struct.unpack_from("<I", new_rom, base + 4 * r)[0]
        m = re.match(r"^(\s+)(.*), // (.*)$", lines[entry_lines[r]])
        if m.group(2) != battle_effect_text(ids, a):
            mism += 1
            if mism <= 5:
                print("   formatter vs source, entry %d: source %r mine %r" % (r, m.group(2), battle_effect_text(ids, a)))
        if a != b:
            changed.append(r)
    print("   formatter mismatches against the stock source: %d" % mism)
    print("   entries to change: %d" % len(changed))
    if check:
        return
    for r in changed:
        b = struct.unpack_from("<I", new_rom, base + 4 * r)[0]
        m = re.match(r"^(\s+)(.*), // (.*)$", lines[entry_lines[r]])
        lines[entry_lines[r]] = "%s%s, // %s" % (m.group(1), battle_effect_text(ids, b), m.group(3))
    open(path, "w", newline="", encoding="utf-8").write(eol.join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ips", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--elf", required=True)
    ap.add_argument("--src", default=alchemy_dir.GAME)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("tables", nargs="*")
    args = ap.parse_args()

    N = Names(os.path.join(args.src, "include"))
    rom = open(args.rom, "rb").read()
    new_rom = apply_ips(rom, args.ips)
    syms = symbols(args.elf)
    report = []
    wanted = args.tables or list(TABLES) + ["battleeffects"]
    for key in wanted:
        if key == "battleeffects":
            port_battle_effects(args, syms, rom, new_rom, args.check)
            continue
        spec = TABLES[key]
        addr, size = syms[spec["symbol"]]
        n = size // spec["rec"]
        if size % spec["rec"]:
            print("WARNING %s: symbol size %d is not a multiple of %d" % (key, size, spec["rec"]))
        base = addr - 0x08000000
        path = os.path.join(args.src, "src", "game", spec["file"])
        text = open(path, newline="", encoding="utf-8").read()
        eol = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(eol)
        rows = parse_rows(lines, spec["decl"])
        print("== %s: %d records in the ROM, %d rows in %s" % (key, n, len(rows), spec["file"]))
        if len(rows) != n:
            print("   ROW COUNT DIFFERS: stock source and ROM do not agree; skipping")
            continue
        # formatter check: render each stock row, compare with the source text
        mism = 0
        changed_rows = []
        reserved_warn = 0
        for r in range(n):
            a = rom[base + r * spec["rec"]: base + (r + 1) * spec["rec"]]
            b = new_rom[base + r * spec["rec"]: base + (r + 1) * spec["rec"]]
            old = decode(spec, a)
            new = decode(spec, b)
            row = rows[r]
            chunks = dict((nm, ls) for nm, ls in row.chunks)
            for name in order_of(spec):
                if name == "name":
                    continue
                want = render(N, spec, name, old[name])
                have = chunks.get(name)
                if want != have:
                    mism += 1
                    if mism <= 6:
                        print("   formatter vs source, row %d %s:\n     source: %s\n     mine:   %s" % (
                            r, name, have, want))
            for (lo, hi) in spec["reserved"]:
                if a[lo:hi] != b[lo:hi]:
                    reserved_warn += 1
                    print("   WARNING row %d: reserved bytes %d..%d differ (%s -> %s); not ported" % (
                        r, lo, hi, a[lo:hi].hex(), b[lo:hi].hex()))
            for pad in ("_abilitypad", "_effectpad"):
                if old.get(pad) != new.get(pad):
                    print("   WARNING row %d: %s differs; not ported" % (r, pad))
            if any(old.get(nm) != new.get(nm) for nm in order_of(spec) if nm != "name"):
                changed_rows.append((r, old, new))
        print("   formatter mismatches against the stock source: %d" % mism)
        print("   rows to change: %d" % len(changed_rows))
        report.append((key, n, len(changed_rows), mism))
        if args.check:
            continue
        # apply bottom-up so line indices stay valid
        for r, old, new in sorted(changed_rows, key=lambda t: -t[0]):
            row = rows[r]
            newlines = rebuild_row(N, spec, row, old, new, lines)
            lines[row.start:row.end + 1] = newlines
        open(path, "w", newline="", encoding="utf-8").write(eol.join(lines))
    if args.report:
        with open(args.report, "w") as fh:
            for key, n, c, m in report:
                fh.write("%s: %d records, %d changed, %d formatter mismatches\n" % (key, n, c, m))


main()

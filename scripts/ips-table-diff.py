#!/usr/bin/env python3
"""Field-level differences an IPS patch makes to the game's data tables.

Usage: ips-table-diff.py PATCH.ips ROM.gba ELF [TABLE ...]

ROM is a build of the *unmodified* game and ELF its symbols (never the owner's dump). The
patch is applied to a copy in memory; each table is split into records (its symbol size
divided by the record size) and every changed record is printed as the fields that
differ. Tables: abilities, classes, items, enemies, presets, characters, djinn.

The output reproduces another author's numbers: write it under build/ (git-ignored), not
into the repository.
"""
import struct
import subprocess
import sys

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


def symbol(elf, name):
    out = subprocess.run(["arm-none-eabi-nm", "-S", elf], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        p = line.split()
        if len(p) == 4 and p[3] == name:
            return int(p[0], 16), int(p[1], 16)
    raise SystemExit("no symbol " + name)


# Each table: symbol, record size, then fields as (offset, struct format, name). A field
# not listed shows as "+0xNN" bytes, so nothing is hidden.
TABLES = {
    "abilities": ("gAbilityDefinitions", 16, [
        (0, "B", "targetMode"), (1, "B", "flags"), (2, "B", "element"), (3, "B", "effect"),
        (4, "B", "icon"), (8, "B", "range"), (9, "B", "ppCost"), (10, "H", "power"),
        (12, "B", "fieldPsynergy")]),
    "enemies": ("gEnemy_Definitions", 84, [
        (16, "H", "hp"), (18, "H", "pp"), (20, "H", "atk"), (22, "H", "def"), (24, "H", "agi"),
        (26, "B", "luck"), (27, "B", "actionCount"), (28, "B", "hpRegen"), (29, "B", "ppRegen"),
        (40, "H", "item0"), (42, "H", "item1"), (44, "H", "item2"), (46, "H", "item3"),
        (52, "B", "elementPreset"), (53, "b", "targetStrategy"), (54, "b", "actionStrategy"),
        (55, "B", "itemActions"),
        (56, "H", "ability0"), (58, "H", "ability1"), (60, "H", "ability2"), (62, "H", "ability3"),
        (64, "H", "ability4"), (66, "H", "ability5"), (68, "H", "ability6"), (70, "H", "ability7"),
        (72, "B", "weak0"), (73, "B", "weak1"), (74, "B", "weak2"),
        (76, "H", "coins"), (78, "h", "item"), (80, "h", "itemChance"), (82, "H", "experience")]),
    "classes": ("gClass_DefinitionTable", None, [
        (4, "B", "req0"), (5, "B", "req1"), (6, "B", "req2"), (7, "B", "req3"),
        (8, "B", "hp"), (9, "B", "pp"), (10, "B", "atk"), (11, "B", "def"), (12, "B", "agi"),
        (13, "B", "luck")]),
    "items": ("gItem_DefinitionTable", None, []),
    "presets": ("gEnemy_ElementPresetTable", None, []),
    "characters": ("gCharacter_DefinitionTable", None, []),
    "djinn": ("gDjinn_DefinitionTable", None, []),
}
COUNTS = {"classes": 203, "items": 0, "presets": 0, "characters": 0, "djinn": 28}


def main():
    patch, rom_path, elf = sys.argv[1:4]
    wanted = sys.argv[4:] or list(TABLES)
    rom = open(rom_path, "rb").read()
    new = apply_ips(rom, patch)
    for key in wanted:
        sym, rec, fields = TABLES[key]
        address, size = symbol(elf, sym)
        if rec is None:
            n = COUNTS.get(key) or 0
            rec = size // n if n else 0
        if not rec:
            # unknown record size: report the changed byte ranges only
            rec = 4
        off = address - 0x08000000
        count = size // rec
        changed = 0
        print("## %s  (%s, %d records of %d bytes)" % (key, sym, count, rec))
        names = {o: (f, n) for o, f, n in fields}
        for r in range(count):
            a = rom[off + r * rec: off + (r + 1) * rec]
            b = new[off + r * rec: off + (r + 1) * rec]
            if a == b:
                continue
            changed += 1
            diffs = []
            covered = set()
            for o, (f, n) in sorted(names.items()):
                w = struct.calcsize("<" + f)
                va = struct.unpack_from("<" + f, a, o)[0]
                vb = struct.unpack_from("<" + f, b, o)[0]
                covered.update(range(o, o + w))
                if va != vb:
                    diffs.append("%s %d -> %d" % (n, va, vb))
            rest = [i for i in range(rec) if a[i] != b[i] and i not in covered]
            if rest:
                diffs.append("bytes " + ", ".join("+%#x %02x->%02x" % (i, a[i], b[i]) for i in rest[:12])
                             + (" ..." if len(rest) > 12 else ""))
            print("- %d: %s" % (r, "; ".join(diffs)))
        print("(%d of %d records changed)\n" % (changed, count))


main()

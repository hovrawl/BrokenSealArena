#!/usr/bin/env python3
"""Compare the data tables of our built ROM with the patched stock ROM, record by record.

Usage: table-check.py --ips PATCH.ips --stock-rom ROM --stock-elf ELF --our-rom ROM --our-elf ELF [TABLE ...]

"Stock" is a build of unmodified upstream (~/alchemy-stock); the Golden Sun Reloaded patch
is applied to it in memory. "Ours" is ~/alchemy's build, whose tables were rewritten by
port-reloaded-tables.py. Each table is found by its symbol in each ELF and split into
records; the records that differ are listed with the offsets of the differing bytes.
Differences should be only ones we can explain (the arena's own edits), so the expected
output is "0 of N differ" for every table that was ported.

Tables: gAbilityDefinitions gClass_DefinitionTable gItem_DefinitionTable
        gEnemy_Definitions gEnemy_ElementPresetTable gCharacter_DefinitionTable
        gDjinn_DefinitionTable (default: all; or the short names from the converter).
Not a table the patch ports: reserved bytes the converter reports (enemy bytes 30 to 39).
Use --ignore-reserved to leave out the bytes listed in IGNORE.

Writes nothing; run it under build/ if you keep the output (it names no numbers except
byte offsets).
"""
import argparse
import subprocess

RECORDS = {
    "gAbilityDefinitions": 16,
    "gClass_DefinitionTable": 84,
    "gItem_DefinitionTable": 44,
    "gEnemy_Definitions": 84,
    "gEnemy_ElementPresetTable": 24,
    "gCharacter_DefinitionTable": 180,
    "gDjinn_DefinitionTable": 12,
    "gAbilityBattleEffects": 4,
}
SHORT = {"abilities": "gAbilityDefinitions", "classes": "gClass_DefinitionTable",
         "items": "gItem_DefinitionTable", "enemies": "gEnemy_Definitions",
         "presets": "gEnemy_ElementPresetTable", "characters": "gCharacter_DefinitionTable",
         "djinn": "gDjinn_DefinitionTable", "battleeffects": "gAbilityBattleEffects"}
# byte ranges inside a record that the converter does not port (unread reserved bytes)
IGNORE = {"gEnemy_Definitions": [(30, 40)]}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ips", required=True)
    ap.add_argument("--stock-rom", required=True)
    ap.add_argument("--stock-elf", required=True)
    ap.add_argument("--our-rom", required=True)
    ap.add_argument("--our-elf", required=True)
    ap.add_argument("--ignore-reserved", action="store_true")
    ap.add_argument("--show", type=int, default=15, help="records to list per table")
    ap.add_argument("tables", nargs="*")
    args = ap.parse_args()

    stock = apply_ips(open(args.stock_rom, "rb").read(), args.ips)
    ours = open(args.our_rom, "rb").read()
    ss = symbols(args.stock_elf)
    os_ = symbols(args.our_elf)
    names = [SHORT.get(t, t) for t in args.tables] or list(RECORDS)
    total_bad = 0
    for name in names:
        rec = RECORDS[name]
        sa, sz = ss[name]
        oa, oz = os_[name]
        n = min(sz, oz) // rec
        if sz != oz:
            print("%s: SIZE differs, stock %d bytes, ours %d" % (name, sz, oz))
        bad = []
        for r in range(n):
            a = stock[sa - 0x08000000 + r * rec: sa - 0x08000000 + (r + 1) * rec]
            b = ours[oa - 0x08000000 + r * rec: oa - 0x08000000 + (r + 1) * rec]
            diff = [i for i in range(rec) if a[i] != b[i]]
            if args.ignore_reserved:
                diff = [i for i in diff if not any(lo <= i < hi for lo, hi in IGNORE.get(name, []))]
            if diff:
                bad.append((r, diff, a, b))
        total_bad += len(bad)
        print("%s: %d of %d records differ" % (name, len(bad), n))
        for r, diff, a, b in bad[:args.show]:
            print("   record %d: bytes %s" % (r, ", ".join("+%d %02x/%02x" % (i, a[i], b[i]) for i in diff[:10])))
    print("total differing records: %d" % total_bad)


main()

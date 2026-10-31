#!/usr/bin/env python3
"""Reads an IPS patch and says which parts of the game it changes.

Usage: ips-regions.py PATCH.ips ELF [--records]

Each IPS record is a byte range of the ROM (offset 0 is 0x08000000). The ELF is a
build of the *unmodified* game, so that its symbols sit where the patch expects them;
`nm` names the symbol each range falls in. Prints bytes changed per symbol, largest
first, and with --records every record. Nothing is read from or written to a ROM.
"""
import subprocess
import sys
from bisect import bisect_right


def records(path):
    data = open(path, "rb").read()
    assert data[:5] == b"PATCH", "not an IPS file"
    i = 5
    while data[i:i + 3] != b"EOF":
        offset = int.from_bytes(data[i:i + 3], "big")
        size = int.from_bytes(data[i + 3:i + 5], "big")
        i += 5
        if size == 0:  # a run of one byte
            size = int.from_bytes(data[i:i + 2], "big")
            payload = data[i + 2:i + 3] * size
            i += 3
        else:
            payload = data[i:i + size]
            i += size
        yield offset, payload


def symbols(elf):
    out = subprocess.run(["arm-none-eabi-nm", "-n", "--defined-only", elf],
                         capture_output=True, text=True, check=True).stdout
    table = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1].lower() in "tdr" and parts[0].startswith("08"):
            table.append((int(parts[0], 16) - 0x08000000, parts[2]))
    return table


def main():
    patch, elf = sys.argv[1], sys.argv[2]
    table = symbols(elf)
    starts = [a for a, _ in table]
    per = {}
    total = 0
    count = 0
    for offset, payload in records(patch):
        count += 1
        total += len(payload)
        k = bisect_right(starts, offset) - 1
        name = table[k][1] if k >= 0 else "(before the first symbol)"
        per.setdefault(name, [0, 0])
        per[name][0] += len(payload)
        per[name][1] += 1
        if "--records" in sys.argv:
            print("%06x %5d  %s+%#x" % (offset, len(payload), name, offset - (table[k][0] if k >= 0 else 0)))
    print("%d records, %d bytes changed\n" % (count, total))
    print("%8s %7s  %s" % ("bytes", "records", "symbol the range starts in"))
    for name, (b, r) in sorted(per.items(), key=lambda kv: -kv[1][0]):
        print("%8d %7d  %s" % (b, r, name))


main()

#!/usr/bin/env python3
"""Prints bytes of the *patched* game at an address, as decimal rows.

Usage: ips-bytes.py PATCH.ips ROM.gba ADDRESS COUNT [WIDTH]
"""
import sys

sys.dont_write_bytecode = True


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
        out[off:off + size] = payload
    return bytes(out)


patch, rom_path, address, count = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4])
width = int(sys.argv[5]) if len(sys.argv) > 5 else 16
blob = apply_ips(open(rom_path, "rb").read(), patch)
base = address - 0x08000000
for i in range(0, count, width):
    row = blob[base + i: base + min(i + width, count)]
    print("%08x: %s" % (address + i, " ".join("%3d" % b for b in row)))

#!/usr/bin/env python3
"""Checks the deterministic level-up rule against a patch's own growth curves.

Usage: levelup-check.py PATCH.ips|- ROM.gba ELF [LEVEL]   (- reads the game's own curves)

Applies the patch in memory, reads each character's growth curves, runs the rule
written in arena_rules.c (ArenaRules_LevelGain) from level 1 to LEVEL (default 99) and
prints the base stats reached, to compare with the rebalance's own documentation (its
Class Documentation workbook has a "Lv99 Character Stats" sheet).
"""
import struct
import subprocess
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


def table(elf):
    for line in subprocess.run(["arm-none-eabi-nm", "-S", elf], capture_output=True, text=True).stdout.splitlines():
        p = line.split()
        if len(p) == 4 and p[3] == "gCharacter_DefinitionTable":
            return int(p[0], 16) - 0x08000000


def div(a, b):  # C division, truncating toward zero
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def gain(diff, level):
    span = 20 if level >= 20 else 19
    return div(level * diff, span) - div((level - 1) * diff, span)


def main():
    patch, rom_path, elf = sys.argv[1:4]
    top = int(sys.argv[4]) if len(sys.argv) > 4 else 99
    rom = open(rom_path, "rb").read()
    if patch != "-":
        rom = apply_ips(rom, patch)
    base = table(elf)
    names = ["Isaac", "Garet", "Ivan", "Mia", "Felix", "Jenna", "Sheba", "Piers"]
    print("%-6s %5s %5s %5s %5s %5s %5s   (base stats at level %d)" % ("", "HP", "PP", "ATK", "DEF", "AGI", "LCK", top))
    for c in range(8):
        rec = rom[base + c * 180: base + (c + 1) * 180]
        curves = []
        for fmt, off in (("<6h", 0x50), ("<6h", 0x5c), ("<6H", 0x68), ("<6H", 0x74), ("<6H", 0x80), ("<6B", 0x8c)):
            curves.append(list(struct.unpack_from(fmt, rec, off)))
        out = []
        for g in curves:
            v = g[0]  # level 1 starts at the first point
            for level in range(1, top + 1):
                band = min(level // 20, 4)
                v += gain(g[band + 1] - g[band], level)
            out.append(v)
        print("%-6s %5d %5d %5d %5d %5d %5d" % tuple([names[c]] + out))


main()

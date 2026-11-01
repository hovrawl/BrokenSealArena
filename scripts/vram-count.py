#!/usr/bin/env python3
"""Reads the output of a smoke run that included vram_peek.txt (decimal 4-byte peeks
of gVramCacheBlockOwners) and prints how many of the 512 sprite VRAM blocks are free."""
import sys
free = used = 0
for line in open(sys.argv[1]):
    if ':' not in line:
        continue
    a, v = line.split(":")[:2]
    try:
        v = int(v)
    except ValueError:
        continue
    if int(a, 16) < 0x03001810 or int(a, 16) >= 0x03001A10:
        continue
    for k in range(4):
        if (v >> (8 * k)) & 255 == 255:
            free += 1
        else:
            used += 1
print("used %d free %d" % (used, free))

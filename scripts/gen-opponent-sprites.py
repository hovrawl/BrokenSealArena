#!/usr/bin/env python3
"""Makes the half-size battle sheets that a linked four-a-side battle draws its
opponents with (ARENA_LINK4): spr_304, 306, 307 and 308 from the characters'
spr_300 to 303. Each 64 x 64 picture of a sheet becomes 32 x 32, so a unit costs
16 blocks of sprite VRAM instead of 64.

Usage: gen-opponent-sprites.py SPRITE_DIR   (games/tbs/src/graphics/sprite)

The sheets are indexed colour; colour 0 is clear. Each 2 x 2 block becomes its
most common solid colour when at least two of its pixels are solid (the later
one wins a tie, which favours outlines drawn last), else clear. The output is
written beside the sources and is not committed: it derives from the game's art.
"""
import sys
from collections import Counter
from PIL import Image

PAIRS = {300: 304, 301: 306, 302: 307, 303: 308}


def halve(src):
    w, h = src.size
    px = src.load()
    dst = Image.new("P", (w // 2, h // 2), 0)
    dst.putpalette(src.getpalette())
    out = dst.load()
    for y in range(h // 2):
        for x in range(w // 2):
            cells = [px[2 * x, 2 * y], px[2 * x + 1, 2 * y],
                     px[2 * x, 2 * y + 1], px[2 * x + 1, 2 * y + 1]]
            solid = [c for c in cells if c != 0]
            if len(solid) < 2:
                continue
            best = max(Counter(solid).items(),
                       key=lambda kv: (kv[1], max(i for i, c in enumerate(cells) if c == kv[0])))
            out[x, y] = best[0]
    return dst


def main():
    directory = sys.argv[1]
    for source, target in PAIRS.items():
        image = Image.open("%s/spr_%03d.png" % (directory, source))
        assert image.mode == "P" and image.size == (64, 1280), image.size
        halve(image).save("%s/spr_%03d.png" % (directory, target))
        print("spr_%03d -> spr_%03d" % (source, target))


main()

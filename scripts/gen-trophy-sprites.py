#!/usr/bin/env python3
"""Makes the arena's trophy sprites (placeholder art, drawn by this script):
spr_309 bronze, 310 silver, 311 gold, 312 gold with a crown and a red gem,
313 blue (side cups). Each is one 16 x 16 picture of a cup standing on a plinth
(16 x 16 costs a quarter of the sprite memory of a person's 32 x 32), and an
animation file whose every animation holds that picture.

Usage: gen-trophy-sprites.py SPRITE_DIR   (games/tbs/src/graphics/sprite)

The sheets are indexed colour in the field sprites' palette (the colour numbers
below are indexes into it: the PNG carries that palette, copied from spr_106).
Colour 0 is clear. The output is written beside the sources and is not
committed (the build runs this script, as it does for the opponent sheets).
"""
import sys
from PIL import Image

W, H = 16, 16
OUTLINE = 217  # 181818

# name: (light, mid, dark, accent)
TIERS = {
    309: (53, 52, 45, 54),     # bronze
    310: (15, 223, 14, 173),   # silver
    311: (30, 24, 11, 4),      # gold
    312: (30, 24, 11, 2),      # gold, crown, red gem
    313: (201, 194, 151, 33),  # blue, green gem (side cups)
}


def build(tier, crown):
    light, mid, dark, accent = TIERS[tier]
    mask = {}  # (x, y) -> colour

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            mask[(x, y)] = c

    def shade(x):
        if x <= 6:
            return light
        if x >= 9:
            return dark
        return mid

    top = 3 if crown else 2
    # bowl: six rows, widest at the rim (x 5 to 10), narrowing to the stem
    halfwidths = [3, 3, 3, 2, 2, 1]
    for i, hw in enumerate(halfwidths):
        y = top + i
        for x in range(int(7.5 - hw + 0.5), int(7.5 + hw - 0.5) + 1):
            put(x, y, shade(x))
    for x in range(5, 11):
        put(x, top, light if x < 8 else mid)
    last = top + len(halfwidths) - 1
    # handles: one pixel each side of the bowl, two rows
    for dy in (1, 2):
        put(4, top + dy, mid)
        put(11, top + dy, dark)
    # stem, ledge, plinth and base
    for y in (last + 1, last + 2):
        put(7, y, light)
        put(8, y, dark)
    for x in range(6, 10):
        put(x, last + 3, mid if x < 8 else dark)
    for y in (last + 4, last + 5):
        for x in range(5, 11):
            put(x, y, shade(x))
    for y in (last + 6, last + 7):
        for x in range(3, 13):
            put(x, y, shade(x))
    # a gem on the bowl
    put(7, top + 2, accent)
    put(8, top + 2, accent)
    if crown:
        # spikes above the rim, the middle two taller with a gem on top
        for sx in (5, 7, 8, 10):
            for y in range(top - 2, top):
                put(sx, y, mid if sx < 8 else dark)
        put(7, top - 3, accent)
        put(8, top - 3, accent)
    # outline: every clear pixel next to a solid one (4-neighbours)
    solid = set(mask)
    for (x, y) in list(solid):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in solid and 0 <= p[0] < W and 0 <= p[1] < H:
                mask[p] = OUTLINE
    return mask


def main():
    directory = sys.argv[1]
    palette = Image.open("%s/spr_106.png" % directory).getpalette()
    for tier in TIERS:
        image = Image.new("P", (W, H), 0)
        image.putpalette(palette)
        px = image.load()
        for (x, y), c in build(tier, tier == 312).items():
            px[x, y] = c
        image.save("%s/spr_%03d.png" % (directory, tier))
        with open("%s/spr_%03d.tsv" % (directory, tier), "w", newline="\n") as f:
            for _ in range(6):
                f.write("anim\tpicture 0 4, hold\n")
        print("spr_%03d" % tier)


main()

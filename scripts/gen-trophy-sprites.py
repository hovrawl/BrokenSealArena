#!/usr/bin/env python3
"""Makes the arena's trophy sprites (placeholder art, drawn by this script), one
design for each of the nine cups, in cup order: spr_309 a cup (bronze), 310 a
pennant (bronze), 311 a shield (silver), 312 a star on a plinth (silver), 313 a
sword in a stone (gold), 315 a laurel wreath (gold), 316 a crown (gold, red
gems), 317 a gem on a plinth (blue), 318 a mask (blue). Each is one 16 x 16
picture (16 x 16 costs a quarter of the sprite memory of a person's 32 x 32), and
an animation file whose every animation holds that picture. Except the first,
the designs are the ASCII pictures in ART (letters are colour roles; a one pixel
outline is added).
spr_314 is the display case the trophies stand in: 16 x 32, a wooden frame with a
glass front on a stone pedestal. A trophy actor is placed 4 pixels above the
case's foot and one pixel in front of it, so the cup sits inside the glass.

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
    309: (53, 52, 45, 54),     # bronze (the cup)
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


def build_case():
    """The display case, 16 x 32: cap (y 1-3), glass (4-27), shelf, a low plinth."""
    mask = {}
    CH = 32
    WOOD_L, WOOD_M, WOOD_D = 52, 211, 18
    BACK, BACK_D, GLASS_L, GLASS_H = 80, 37, 202, 209
    STONE_L, STONE_M, STONE_D = 223, 222, 219

    def put(x, y, c):
        mask[(x, y)] = c

    for x in range(0, 16):  # cornice
        put(x, 1, WOOD_L)
        put(x, 2, WOOD_M if 0 < x < 15 else WOOD_D)
    for x in range(1, 15):
        put(x, 3, WOOD_D)
    for y in range(4, 28):  # sides and the glass
        for x in (1, 2):
            put(x, y, WOOD_L if x == 1 else WOOD_M)
        for x in (13, 14):
            put(x, y, WOOD_M if x == 13 else WOOD_D)
        for x in range(3, 13):
            put(x, y, BACK_D if y == 4 else BACK)
    for k in range(4):  # glints on the glass
        put(10 + k // 2 + (k % 2), 6 - k // 2 + (k % 2), GLASS_H)
    for dy in range(5):
        put(3, 6 + dy, GLASS_L)
    for x in range(1, 15):  # shelf and the frame's foot
        put(x, 28, WOOD_L)
        put(x, 29, WOOD_D)
    for x in range(0, 16):  # pedestal lip and body
        put(x, 30, STONE_L)
    for y in range(31, 32):
        for x in range(1, 15):
            put(x, y, STONE_L if x < 5 else (STONE_D if x > 10 else STONE_M))
    solid = set(mask)
    for (x, y) in list(solid):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in solid and 0 <= p[0] < W and 0 <= p[1] < CH:
                mask[p] = OUTLINE
    return mask



# Colour roles of the ASCII pictures: L M D light, mid, dark and A accent of the
# design's tier colours; the rest are fixed palette indexes.
FIXED = {'S': 223, 's': 222, 'T': 219,   # stone
         'G': 33, 'g': 20, 'h': 50,      # leaves
         'R': 2, 'Y': 30, 'y': 24,       # red, gold, dark gold
         'W': 15, 'w': 14}               # blade

PLINTH = [
    "...SSSSSSSSsT...",
    "..SSSSSSSSssTT..",
    "..SSSSSSSSssTT..",
    "..TTTTTTTTTTTT..",
]

ART = {
    310: ((53, 52, 45, 54), True, [                    # pennant on a plinth
        "................",
        ".....yLLLLLLLM..",
        ".....yLLLLLLMD..",
        ".....yLLLLMMDD..",
        ".....yLLMMMDD...",
        ".....yLMMDD.....",
        ".....yMDD.......",
        ".....y..........",
        ".....y..........",
        ".....y..........",
        ".....y..........",
    ]),
    311: ((15, 223, 14, 2), False, [                   # shield with a cross
        "................",
        "..LLLLLAADDDDD..",
        "..LLLLLAADDDDD..",
        "..LAAAAAAAAAAD..",
        "..LAAAAAAAAAAD..",
        "..LLLLLAADDDDD..",
        "..LLLLLAADDDDD..",
        "...LLLLAADDDD...",
        "...LLLLAADDDD...",
        "....LLLAADDD....",
        ".....LLAADD.....",
        "......LAAD......",
        ".......AD.......",
    ]),
    312: ((15, 223, 14, 173), True, [                  # star on a plinth
        "................",
        ".......LD.......",
        "......LLDD......",
        "......LMMD......",
        ".LLLLLLMMDDDDDD.",
        "..LLLLLMMDDDDD..",
        "....LLLMMDDD....",
        "....LLMMMMDD....",
        "...LLLM..MDDD...",
        "...LL......DD...",
        "................",
    ]),
    313: ((30, 24, 11, 2), False, [                    # sword in a stone
        "................",
        ".......Ww.......",
        ".......Ww.......",
        ".......Ww.......",
        ".......Ww.......",
        ".......Ww.......",
        ".......Ww.......",
        ".......Ww.......",
        "....YYYYYYyy....",
        ".......yy.......",
        ".......yy.......",
        "..SSSSSSSSssTT..",
        ".SSSSSSSSSsssTT.",
        ".SSSSssssssTTTT.",
        "..TTTTTTTTTTTT..",
    ]),
    315: ((30, 24, 11, 2), False, [                    # laurel wreath
        "................",
        "....GGG..hhh....",
        "..GGggG..hggGG..",
        ".GGgG......hggG.",
        ".GgG........GgG.",
        ".GgG........GgG.",
        ".GgG........hgG.",
        ".GGg........ggG.",
        ".hGGg......gGGh.",
        "..hGGg....gGGh..",
        "...hGGgRRgGGh...",
        "....hhYYYYhh....",
        ".....YY..YY.....",
        "....YY....YY....",
    ]),
    316: ((30, 24, 11, 2), True, [                     # crown with red gems
        "................",
        "..LL...MM...DD..",
        "..LL...MM...DD..",
        "..LLL.MMMM.DDD..",
        "..LLLLMMMMDDDD..",
        "..LLLLMMMMDDDD..",
        "..LAALMMMDAADD..",
        "..LLLLMMMMDDDD..",
        "..LLLLLMMDDDDD..",
        "..LLLLMMMMDDDD..",
        "................",
    ]),
    317: ((215, 207, 201, 15), True, [                 # gem on a plinth
        "................",
        "....LLLLMMDD....",
        "...LLLLLMMDDD...",
        "..LLLLLLMMDDDD..",
        "..AAAAAAAAAAAA..",
        "...LLLLMMDDDD...",
        "....LLLMMMDD....",
        ".....LLMMDD.....",
        "......LMDD......",
        ".......MD.......",
        "................",
    ]),
    318: ((201, 194, 151, 33), True, [                 # mask
        "................",
        "..LLLLLMMDDDDD..",
        "..LLLLLMMDDDDD..",
        "..LLLLLAADDDDD..",
        "..LLL..MM..DDD..",
        "..LLL..MM..DDD..",
        "..LLLLLMMDDDDD..",
        "...LLLLMMDDDD...",
        "....LL.MM.DD....",
        ".....LLMMDD.....",
        "................",
    ]),
}


def build_art(tier):
    colours, plinth, rows = ART[tier]
    roles = dict(FIXED)
    roles.update(zip("LMDA", colours))
    rows = list(rows)
    if plinth:
        rows += PLINTH
    mask = {}
    for y, row in enumerate(rows):
        assert len(row) == W, (tier, y, row)
        for x, ch in enumerate(row):
            if ch != '.':
                mask[(x, y)] = roles[ch]
    assert max(y for (_, y) in mask) < H, tier
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
    for tier in [309] + sorted(ART):
        image = Image.new("P", (W, H), 0)
        image.putpalette(palette)
        px = image.load()
        picture = build(tier, False) if tier == 309 else build_art(tier)
        for (x, y), c in picture.items():
            px[x, y] = c
        image.save("%s/spr_%03d.png" % (directory, tier))
        with open("%s/spr_%03d.tsv" % (directory, tier), "w", newline="\n") as f:
            for _ in range(6):
                f.write("anim\tpicture 0 4, hold\n")
        print("spr_%03d" % tier)
    image = Image.new("P", (W, 32), 0)
    image.putpalette(palette)
    px = image.load()
    for (x, y), c in build_case().items():
        px[x, y] = c
    image.save("%s/spr_314.png" % directory)
    with open("%s/spr_314.tsv" % directory, "w", newline="\n") as f:
        for _ in range(6):
            f.write("anim\tpicture 0 4, hold\n")
    print("spr_314")


main()

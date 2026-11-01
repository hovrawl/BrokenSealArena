"""Scratch: name, type, price and equipMask of the given ITEM_ constants (argv), from item_table.c."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alchemy_dir

t = open(os.path.join(alchemy_dir.GAME, "src/game/item_table.c"), encoding="utf-8").read()
for want in sys.argv[1:]:
    m = re.search(r"\n    // ([^\n]*)\n    \{\n(.*?)\n    \},", t, re.S) and None
    for m in re.finditer(r"\n    // ([^\n]*)\n    \{\n(.*?)\n    \},", t, re.S):
        const = "ITEM_" + re.sub(r"[^A-Z0-9]+", "_", m.group(1).upper().replace("'", "")).strip("_")
        if const == want:
            b = m.group(2)
            g = lambda f: (re.search(r"\.%s = ([^,\n]+)" % f, b) or [0, "-"])[1]
            print("%-24s %-16s %6s %-22s atk/def %s %s" % (want, g("type")[10:], g("price"), g("equipMask"),
                  g("attack"), g("defense")))

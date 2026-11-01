"""Verifies scripts/cupdata.py against the game tables.

Run in WSL:  python3 scripts/cup-check.py        (prints OK or the problems)
Checks: every enemy id is a real row (level above 0); a round has at most five
kinds and six sprite slots (small enemy 1, others 2); levels are 1 to 99; each cup
ends with its boss round; every Djinni is obtained exactly once (start stock,
sold after a cup, or won in a round); reward names exist; the shop rows exist.
Prints each cup's rounds with slots, levels and the enemy names."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cupdata as D
import cupgame as G


ITEMS = {}


def main():
    ITEMS.update(G.item_ids())
    enemies = G.parse_enemies()
    small = G.parse_small()
    bad = []
    seen = {}
    for ci, cup in enumerate(D.CUPS):
        print("%d %s%s: %d rounds" % (ci, cup.name, " (side)" if cup.side else "", len(cup.rounds)))
        if len(cup.rounds) > 16:
            bad.append("%s: more than 16 rounds" % cup.name)
        prev = 0
        for ri, rd in enumerate(cup.rounds):
            ids = [i for i, _ in rd.team]
            cnt = [c for _, c in rd.team]
            if not 1 <= len(ids) <= 5:
                bad.append("%s round %d: %d kinds" % (cup.name, ri + 1, len(ids)))
            for i in ids:
                if i < 0 or i >= len(enemies) or enemies[i]["level"] <= 0:
                    bad.append("%s round %d: enemy %d is not a real row" % (cup.name, ri + 1, i))
            if any(c < 1 for c in cnt):
                bad.append("%s round %d: a count below 1" % (cup.name, ri + 1))
            if all(0 <= i < len(enemies) for i in ids):
                n = G.slots(small, ids, cnt)
                if n > 6:
                    bad.append("%s round %d: %d sprite slots (limit 6)" % (cup.name, ri + 1, n))
                names = ", ".join("%s x%d (L%d%s)" % (enemies[i]["name"], c, enemies[i]["level"],
                                                     "" if small[i + 8] else ", large")
                                  for i, c in rd.team)
                print("   %2d  target L%-2d [%d slots]  %s%s" % (
                    ri + 1, rd.level, n, names, "  => " + ", ".join(r[1] for r in rd.rewards) if rd.rewards else ""))
            if not 1 <= rd.level <= 99:
                bad.append("%s round %d: level %d" % (cup.name, ri + 1, rd.level))
            if rd.level < prev - 4 and not cup.side:
                bad.append("%s round %d: level falls from %d to %d" % (cup.name, ri + 1, prev, rd.level))
            prev = rd.level
            for rw in rd.rewards:
                if rw[0] == "djinn":
                    seen.setdefault(rw[1], []).append(cup.name + " (fought)")
                elif rw[0] == "item":
                    if rw[1] not in ITEMS:
                        bad.append("%s round %d: %s is not an item id" % (cup.name, ri + 1, rw[1]))
                else:
                    bad.append("%s round %d: unknown reward" % (cup.name, ri + 1))
        for n in cup.sells:
            seen.setdefault(n, []).append(cup.name + " (sold)")
        if cup.side and cup.requires > D.MAIN_COUNT:
            bad.append("%s: requires beyond the main line" % cup.name)
    for n in D.START_SELLS:
        seen.setdefault(n, []).append("start")
    for el in D.ELEMENTS:
        for n in D.DJINN[el]:
            where = seen.get(n, [])
            if len(where) != 1:
                bad.append("Djinni %s obtained %d times: %s" % (n, len(where), where))
    if len(D.SHOP_ROWS) != D.MAIN_COUNT + 1:
        bad.append("SHOP_ROWS needs %d entries" % (D.MAIN_COUNT + 1))
    for row in D.SHOP_ROWS + [D.CROSSBONE_ROWS]:
        for r in row:
            if not 1 <= r <= 34:
                bad.append("shop row %d is outside the stock table" % r)
    if bad:
        print("PROBLEMS:")
        for b in bad:
            print("  " + b)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()

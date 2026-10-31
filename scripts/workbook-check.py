#!/usr/bin/env python3
"""Spot-check our C tables against the Reloaded authors' Excel documentation.

Usage: workbook-check.py [--src ~/alchemy/games/tbs] [--dir reloaded]

Reads the workbooks in reloaded/ (git-ignored, see docs/RELOADED.md) with xlsx-overview.py
and compares what they state with the values in our ability, item and class tables:

- Psynergy Documentation.xlsx, "Base Damage Spells, Heal, Buffs": each spell's PP and
  power (the sheet's name is matched to the table row's comment, the English name).
- Items, Equipment, & Unleash Documentation.xlsx: weapon attack and price, by name.
- Class Documentation.xlsx: class multipliers, by class name (the sheet shows them as
  fractions of 1; ours are in twentieths).

It prints the number it compared and every difference, so the output is the spot check.
Names the table does not carry (the English names of renamed rows are not in our comments
until the text port) are listed as "no row".
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sheet(book, name):
    out = subprocess.run([sys.executable, os.path.join(HERE, "xlsx-overview.py"), book, "--sheet", name],
                         capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines()]


def sheets(book):
    out = subprocess.run([sys.executable, os.path.join(HERE, "xlsx-overview.py"), book, "0"],
                         capture_output=True, text=True, check=True).stdout
    return [m.group(1).strip() for m in re.finditer(r"^== (.*?)\s+\(\d+ non-empty rows", out, flags=re.M)]


def to_int(s):
    s = s.strip().replace(",", ".")
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f == int(f) else None


def rows_of(path, decl):
    """[(comment, {field: text})] for the rows of a table file."""
    lines = open(path, encoding="utf-8").read().split("\n")
    d = next(i for i, l in enumerate(lines) if decl in l and l.rstrip().endswith("{") and "=" in l)
    rows = []
    i = d + 1
    while not lines[i].startswith("};"):
        if lines[i].startswith("    {"):
            comment = lines[i - 1].strip()[3:] if lines[i - 1].startswith("    //") else ""
            fields = {}
            j = i
            if not lines[i].rstrip().endswith("},"):
                j = i + 1
                while lines[j] != "    },":
                    m = re.match(r"^        \.(\w+) = (.*?),?$", lines[j])
                    if m:
                        fields[m.group(1)] = m.group(2).rstrip(",")
                    j += 1
            rows.append((comment, fields))
            i = j + 1
        else:
            i += 1
    return rows


def num(fields, key):
    v = fields.get(key, "0")
    try:
        return int(v, 0)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser("~/alchemy/games/tbs"))
    ap.add_argument("--dir", default=os.path.join(HERE, "..", "reloaded"))
    args = ap.parse_args()
    game = os.path.join(args.src, "src", "game")

    abilities = rows_of(os.path.join(game, "ability_table.c"), "gAbilityDefinitions")
    items = rows_of(os.path.join(game, "item_table.c"), "gItem_DefinitionTable")
    classes = rows_of(os.path.join(game, "class_table.c"), "gClass_DefinitionTable")

    # --- Psynergy
    book = os.path.join(args.dir, "Psynergy Documentation.xlsx")
    compared = 0
    bad = []
    missing = []
    for row in sheet(book, "Base Damage Spells, Heal, Buffs"):
        for i in range(len(row) - 5):
            n, lvl, name, area, pp, power = row[i:i + 6]
            if to_int(n) is None or not name.strip() or to_int(pp) is None or to_int(power) is None:
                continue
            name = name.strip()
            cands = [a for a in abilities if a[0] == name]
            if not cands:
                missing.append(name)
                continue
            compared += 1
            ok = any(num(a[1], "ppCost") == to_int(pp) and num(a[1], "power") == to_int(power) for a in cands)
            if not ok:
                bad.append("%s: sheet PP %s power %s; table %s" % (
                    name, pp, power, [(num(a[1], "ppCost"), num(a[1], "power")) for a in cands]))
    print("Psynergy: %d spells compared, %d differ, %d names not in the table" % (compared, len(bad), len(missing)))
    for b in bad:
        print("   " + b)
    if missing:
        print("   no row: " + ", ".join(missing))

    # --- Items: "Name | +N | ... | price" blocks on the weapon and armour sheets
    book = os.path.join(args.dir, "Items, Equipment, & Unleash Documentation.xlsx")
    byname = {}
    for c, f in items:
        byname.setdefault(c, []).append(f)
    for sname, key, label in (("Weapon Documentation", "primaryBonus", "attack"),
                              ("Armor Documentation", "secondaryBonus", "defense")):
        compared = 0
        bad = []
        for row in sheet(book, sname):
            cells = [c.strip() for c in row]
            for i in range(len(cells) - 1):
                name = cells[i]
                m = re.fullmatch(r"\+(\d+)", cells[i + 1])
                if name not in byname or not m:
                    continue
                value = int(m.group(1))
                price = None
                for c in cells[i + 2:i + 12]:
                    if c in byname:
                        break
                    if re.fullmatch(r"\d+", c):
                        price = int(c)
                        break
                if price is None:
                    continue
                compared += 1
                ok = any(num(f, key) == value and num(f, "price") == price for f in byname[name])
                if not ok:
                    bad.append("%s: sheet %s %d price %d; table %s" % (
                        name, label, value, price, [(num(f, key), num(f, "price")) for f in byname[name]]))
        print("%s: %d items compared, %d differ" % (sname, compared, len(bad)))
        for b in bad[:30]:
            print("   " + b)
    # --- Classes: "Class Growth" holds the multipliers as fractions; ours are twentieths
    book = os.path.join(args.dir, "Class Documentation.xlsx")
    cbyname = {}
    for c, f in classes:
        cbyname.setdefault(c, []).append(f)
    compared = 0
    bad = []
    for row in sheet(book, "Class Growth"):
        cells = [c.strip() for c in row]
        for i in range(len(cells) - 6):
            name = cells[i]
            if name not in cbyname:
                continue
            try:
                vals = [round(float(c.replace(",", ".")) * 20) for c in cells[i + 1:i + 7]]
            except ValueError:
                continue
            compared += 1
            ok = any([num(f, k) for k in ("hp", "pp", "atk", "def", "agi", "luck")] == vals for f in cbyname[name])
            if not ok:
                others = [c for c, f in classes
                          if [num(f, k) for k in ("hp", "pp", "atk", "def", "agi", "luck")] == vals]
                bad.append("%s: sheet %s; table %s; the same numbers are in the row named %s" % (
                    name, vals, [[num(f, k) for k in ("hp", "pp", "atk", "def", "agi", "luck")] for f in cbyname[name]],
                    others or "(none)"))
    print("Class Growth: %d classes compared, %d differ by name (the Reloaded text renames classes; the row with the same numbers is shown)" % (compared, len(bad)))
    for b in bad[:30]:
        print("   " + b)


main()

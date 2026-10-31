#!/usr/bin/env python3
"""Lists the sheets of Excel workbooks, or dumps one sheet, using only the standard library.

Usage: xlsx-overview.py BOOK.xlsx [ROWS]            sheets, their size and the first ROWS rows
       xlsx-overview.py BOOK.xlsx --sheet NAME      the whole sheet as tab-separated text

An .xlsx is a zip of XML: shared strings, and one XML file per sheet. Formulas show
their last calculated value; merged cells and formatting are ignored.
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def column(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def load(path):
    z = zipfile.ZipFile(path)
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", NS):
            strings.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    sheets = {}
    for s in workbook.find("m:sheets", NS):
        rid = s.get("{%s}id" % NS["r"])
        name = target[rid].lstrip("/")
        sheets[s.get("name")] = name if name.startswith("xl/") else "xl/" + name
    return z, strings, sheets


def rows_of(z, strings, part):
    root = ET.fromstring(z.read(part))
    for row in root.iter("{%s}row" % NS["m"]):
        cells = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if c.get("t") == "inlineStr":
                text = "".join(t.text or "" for t in c.iter("{%s}t" % NS["m"]))
            elif v is None:
                continue
            elif c.get("t") == "s":
                text = strings[int(v.text)]
            else:
                text = v.text
                try:
                    f = float(text)
                    text = str(int(f)) if f == int(f) else ("%.4g" % f)
                except ValueError:
                    pass
            cells[column(c.get("r"))] = text
        if cells:
            yield [cells.get(i, "") for i in range(max(cells) + 1)]


def main():
    z, strings, sheets = load(sys.argv[1])
    if len(sys.argv) > 3 and sys.argv[2] == "--sheet":
        for row in rows_of(z, strings, sheets[sys.argv[3]]):
            print("\t".join(row))
        return
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for name, part in sheets.items():
        rows = list(rows_of(z, strings, part))
        print("== %s  (%d non-empty rows, widest %d cols)" % (name, len(rows), max((len(r) for r in rows), default=0)))
        for row in rows[:count]:
            print("   | " + " | ".join(c[:24] for c in row[:12]))


main()

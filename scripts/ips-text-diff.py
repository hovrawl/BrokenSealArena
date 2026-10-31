#!/usr/bin/env python3
"""Decode the game's messages from a patched ROM and write the changed ones into a .po.

Usage: ips-text-diff.py PATCH.ips ROM.gba ELF EN.po [--list] [--write OUT.po]

ROM and ELF are an unmodified build (never the owner's dump). The message archive is the one
tools/ags-text/archive.c builds: one Huffman model per preceding symbol (symbol 0 starts and
ends a message), message bodies in groups of 256 with their lengths, LSB-first bits. This reads
it back, in the stock ROM and in the patched one, turns each symbol list into the PO's own
notation (the inverse of tools/ags-text/symbols.c for the English alphabet), and compares:

- the stock messages decoded here against EN.po: they must agree, which proves the decoder
  and the notation (the report says how many do not);
- the messages the patch changes, listed with --list and, with --write, written into OUT.po
  (msgctxt and msgid are kept; only the msgstr is replaced).

Writes nothing but OUT.po. The decoded text of another author's work is not committed from
here except as the .po the game builds from: that is the port.
"""
import argparse
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True

# ---- the same helpers as the table scripts

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
        if off + size > len(out):
            out.extend(b"\xff" * (off + size - len(out)))
        out[off:off + size] = payload
    return bytes(out)


def symbols(elf):
    out = subprocess.run(["arm-none-eabi-nm", "-S", elf], capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) == 4:
            table[p[3]] = (int(p[0], 16), int(p[1], 16))
        elif len(p) == 3:
            table[p[2]] = (int(p[0], 16), 0)
    return table


# ---- the archive

class Archive:
    def __init__(self, rom, syms):
        self.rom = rom
        self.contexts = syms["Text_MessageContexts"][0] - 0x08000000
        self.banks = syms["Text_MessageBanks"][0] - 0x08000000
        self.trees = {}

    def u16(self, o):
        return struct.unpack_from("<H", self.rom, o)[0]

    def u32(self, o):
        return struct.unpack_from("<I", self.rom, o)[0]

    def model(self, ctx):
        """The Huffman tree of context `ctx` as nested tuples (symbol,) or (left, right); None if empty."""
        if ctx in self.trees:
            return self.trees[ctx]
        group, within = divmod(ctx, 256)
        base = self.u32(self.contexts + 8 * group) - 0x08000000
        offsets = self.u32(self.contexts + 8 * group + 4) - 0x08000000
        off = self.u16(offsets + 2 * within)
        if off == 0x8000:
            self.trees[ctx] = None
            return None
        p = base + off
        # tree shape: preorder bits from p, LSB first; 1 is a leaf
        bitpos = [0]

        def bit():
            b = (self.rom[p + bitpos[0] // 8] >> (bitpos[0] % 8)) & 1
            bitpos[0] += 1
            return b

        shape_count = [0]

        def shape():
            if bit():
                shape_count[0] += 1
                return ("L",)
            return (shape(), shape())

        shp = shape()
        count = shape_count[0]
        groups = (count + 1) // 2
        leaves = []
        for k in range(groups):
            odd_last = (k == groups - 1) and (count % 2 == 1)
            start = p - 3 * (k + 1) + (1 if odd_last else 0)
            if odd_last:
                b0, b1 = self.rom[start], self.rom[start + 1]
                leaves.append((b0 >> 4) | (b1 << 4))
            else:
                b0, b1, b2 = self.rom[start], self.rom[start + 1], self.rom[start + 2]
                leaves.append((b1 >> 4) | (b2 << 4))
                leaves.append(b0 | ((b1 & 15) << 8))
        it = iter(leaves)

        def fill(node):
            if node == ("L",):
                return (next(it),)
            return (fill(node[0]), fill(node[1]))

        tree = fill(shp)
        self.trees[ctx] = tree
        return tree

    def message(self, number):
        """The symbol list of message `number`, or None for a null message."""
        group, j = divmod(number, 256)
        payload = self.u32(self.banks + 8 * group) - 0x08000000
        lengths = self.u32(self.banks + 8 * group + 4) - 0x08000000
        # lengths: chains of 255s ending in a byte below 255
        pos = lengths
        start = 0
        n = 0
        for idx in range(j + 1):
            length = 0
            while True:
                b = self.rom[pos]
                pos += 1
                length += b
                if b != 255:
                    break
            if idx < j:
                start += length
            else:
                n = length
        if n == 0:
            return None
        data = self.rom[payload + start: payload + start + n]
        out = []
        ctx = 0
        bitpos = 0
        while True:
            tree = self.model(ctx)
            node = tree
            while len(node) == 2:
                b = (data[bitpos // 8] >> (bitpos % 8)) & 1
                bitpos += 1
                node = node[b]
            sym = node[0]
            if sym == 0:
                return out
            out.append(sym)
            ctx = sym

    def count(self):
        return 0


# ---- symbols <-> the PO notation (English alphabet)

COMMANDS = {1: "page_break", 2: "end_wait", 3: "line_break", 4: "pause_60", 5: "pause_20_skippable",
            6: "pause_120_skippable", 7: "reset_text_style", 8: "text_color", 9: "text_effect",
            12: "control_12", 15: "control_15", 16: "protagonist_name", 17: "actor_name",
            18: "argument_actor_name", 19: "argument_class_name", 20: "argument_item_name",
            21: "argument_ability_name", 22: "argument_signed_number", 23: "argument_location_name",
            24: "em_dash", 25: "plural_suffix", 26: "button_icon", 27: "possessive_suffix",
            28: "control_28", 29: "article_class", 30: "end_now"}
TAKES = {8, 9, 12, 15, 17, 18, 19, 20, 26, 28, 29}
COLORS = {3: "red", 5: "yellow", 9: "blue", 16: "white"}
CP1252 = [0x20ac, 0x81, 0x201a, 0x192, 0x201e, 0x2026, 0x2020, 0x2021, 0x2c6, 0x2030, 0x160, 0x2039, 0x152,
          0x8d, 0x17d, 0x8f, 0x90, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014, 0x2dc, 0x2122,
          0x161, 0x203a, 0x153, 0x9d, 0x17e, 0x178]


def to_po(syms):
    """The PO text of a symbol list: a line break is a newline; other controls are {name}."""
    out = []
    i = 0
    while i < len(syms):
        s = syms[i]
        i += 1
        if s == 3:
            out.append("\n")
        elif s < 32:
            name = COMMANDS.get(s)
            if name is None:
                out.append("{control:%d}" % s)
            elif s in TAKES and i < len(syms):
                arg = syms[i]
                i += 1
                if s == 8 and arg in COLORS:
                    out.append("{%s:%s}" % (name, COLORS[arg]))
                else:
                    out.append("{%s:%d}" % (name, arg))
            else:
                out.append("{%s}" % name)
        elif s == ord("{"):
            out.append("{{")
        elif s == ord("}"):
            out.append("}}")
        elif s < 128 or 160 <= s <= 255:
            out.append(chr(s))
        elif 128 <= s < 160:
            out.append(chr(CP1252[s - 128]))
        else:
            out.append("{glyph:%x}" % s)
    return "".join(out)


# ---- the PO file

def unquote(s):
    s = s.strip()
    assert s.startswith('"') and s.endswith('"'), s
    return (s[1:-1].replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            .replace('\\t', '\t').replace('\\r', '\r'))


def quote_lines(text):
    """The msgstr lines for a text: one quoted line per display line."""
    def esc(t):
        return t.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t")
    parts = []
    cur = ""
    for ch in text:
        cur += ch
        if ch == "\n":
            parts.append(cur)
            cur = ""
    if cur or not parts:
        parts.append(cur)
    if len(parts) == 1:
        return ['msgstr "%s"' % esc(parts[0]).replace("\n", "\\n")]
    return ['msgstr ""'] + ['"%s"' % esc(p).replace("\n", "\\n") for p in parts]


def read_po(path):
    """[(ctxt, msgid, msgstr_text, (first_line, last_line))] in file order."""
    lines = open(path, encoding="utf-8").read().split("\n")
    entries = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("msgctxt"):
            start = i
            ctxt = unquote(lines[i].split(" ", 1)[1])
            i += 1
            msgid = unquote(lines[i].split(" ", 1)[1])
            i += 1
            assert lines[i].startswith("msgstr")
            text = unquote(lines[i].split(" ", 1)[1])
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                text += unquote(lines[i])
                i += 1
            entries.append((ctxt, msgid, text, (start, i - 1)))
        else:
            i += 1
    return lines, entries


# table file, first name message (msg_ids.h), the messages' role
COMMENT_TABLES = [("ability_table.c", [819]), ("item_table.c", [117, 386]), ("class_table.c", [1857]),
                  ("enemy_table.c", [655]), ("djinn_table.c", [1119])]


def rename_comments(src, old_archive, new_archive, n):
    """Each row of a table has a `// Name` comment, the English name. Where the patch renames
    the row's message and the comment is still the old name, write the new name."""
    import os
    for fname, bases in COMMENT_TABLES:
        path = os.path.join(src, "src", "game", fname)
        lines = open(path, encoding="utf-8", newline="").read().split("\n")
        rows = [i for i, l in enumerate(lines) if l.startswith("    {") and i and lines[i - 1].startswith("    //")]
        best = None
        for base in bases:
            hits = 0
            for r, i in enumerate(rows):
                m = old_archive.message(base + r) if base + r < n else None
                if m is not None and "// " + to_po(m) == lines[i - 1].strip():
                    hits += 1
            if best is None or hits > best[1]:
                best = (base, hits)
        base = best[0]
        changed = 0
        for r, i in enumerate(rows):
            if base + r >= n:
                break
            o = old_archive.message(base + r)
            nw = new_archive.message(base + r)
            if o == nw or o is None or nw is None:
                continue
            if lines[i - 1].strip() == "// " + to_po(o):
                lines[i - 1] = "    // " + to_po(nw).replace("\n", " ")
                changed += 1
        print("%s: comments renamed %d (message base %d, %d of %d comments matched the old names)" % (
            fname, changed, base, best[1], len(rows)))
        open(path, "w", encoding="utf-8", newline="").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ips")
    ap.add_argument("rom")
    ap.add_argument("elf")
    ap.add_argument("po")
    ap.add_argument("--stock-po", help="the unmodified build's .po: messages past its count are ours and are not compared")
    ap.add_argument("--comments", help="games/tbs directory: rename each table row's comment to the patched name")
    ap.add_argument("--ours", nargs=2, metavar=("ROM", "ELF"), help="our built ROM and ELF: check its messages against the patched stock")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--write")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    stock = open(args.rom, "rb").read()
    patched = apply_ips(stock, args.ips)
    syms = symbols(args.elf)
    a = Archive(stock, syms)
    b = Archive(patched, syms)
    lines, entries = read_po(args.po)
    by_number = {}
    for e in entries:
        if e[1].isdigit():
            by_number[int(e[1])] = e
    n = max(by_number) + 1
    stock_n = n
    if args.stock_po:
        _, stock_entries = read_po(args.stock_po)
        stock_n = max(int(e[1]) for e in stock_entries if e[1].isdigit()) + 1
    print("messages: %d in the .po, %d in the unmodified build" % (n, stock_n))
    n = stock_n

    # 1. the decoder against the .po (stock)
    bad = []
    for i in range(n):
        s = a.message(i)
        want = by_number[i][2]
        got = "" if s is None else to_po(s)
        if got != want:
            bad.append(i)
    print("stock decoded vs the .po: %d of %d differ" % (len(bad), n))
    for i in bad[:8]:
        s = a.message(i)
        print("   %d: po %r\n       me %r" % (i, by_number[i][2][:90], ("" if s is None else to_po(s))[:90]))

    # 2. the patch
    changed = []
    for i in range(n):
        if a.message(i) != b.message(i):
            changed.append(i)
    print("messages the patch changes: %d" % len(changed))
    if args.list:
        for i in changed[:args.limit or None]:
            old = by_number[i][2]
            s = b.message(i)
            new = "" if s is None else to_po(s)
            print("--- %d [%s]\n  old: %r\n  new: %r" % (i, by_number[i][0], old[:200], new[:200]))
    if args.ours:
        # 3. our built ROM against the patched stock: the same messages, up to the stock count
        ours_rom = open(args.ours[0], "rb").read()
        c = Archive(ours_rom, symbols(args.ours[1]))
        differ = [i for i in range(n) if b.message(i) != c.message(i)]
        print("our ROM's messages vs the patched stock, first %d: %d differ" % (n, len(differ)))
        for i in differ[:10]:
            print("   %d: patched %r\n       ours    %r" % (i, to_po(b.message(i) or [])[:80], to_po(c.message(i) or [])[:80]))
    if args.comments:
        rename_comments(args.comments, a, b, n)
    if args.write:
        out = list(lines)
        # replace bottom-up so line numbers stay valid
        for i in sorted(changed, reverse=True):
            first, last = by_number[i][3]
            # find the msgstr line within the entry
            k = first
            while not out[k].startswith("msgstr"):
                k += 1
            s = b.message(i)
            new = "" if s is None else to_po(s)
            out[k:last + 1] = quote_lines(new)
        open(args.write, "w", encoding="utf-8", newline="").write("\n".join(out))
        print("wrote " + args.write)


main()

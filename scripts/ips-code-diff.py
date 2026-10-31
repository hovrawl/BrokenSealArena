#!/usr/bin/env python3
"""Shows how an IPS patch changes the code of named functions, as Thumb assembly.

Usage: ips-code-diff.py PATCH.ips ROM.gba ELF FUNCTION [FUNCTION ...]

ROM is a build of the *unmodified* game (never the owner's cartridge dump) and ELF its
symbols. The patch is applied to a copy in memory; each function's bytes before and after
are disassembled and the differing lines printed with addresses. Functions that are
ARM rather than Thumb will read as nonsense, which shows as a long diff.
"""
import difflib
import subprocess
import sys
import tempfile
import os


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


def symbol(elf, name):
    out = subprocess.run(["arm-none-eabi-nm", "-S", elf], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        p = line.split()
        if len(p) == 4 and p[3] == name:
            return int(p[0], 16), int(p[1], 16)
    raise SystemExit("no symbol " + name)


def disassemble(blob, address):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(blob)
        path = f.name
    try:
        text = subprocess.run(
            ["arm-none-eabi-objdump", "-D", "-b", "binary", "-m", "arm", "-M", "force-thumb",
             "--adjust-vma=%#x" % address, path], capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    lines = []
    for line in text.splitlines():
        if ":\t" in line:
            addr, rest = line.split(":\t", 1)
            lines.append((addr.strip(), "\t".join(rest.split("\t")[1:]).strip() if rest.count("\t") else rest))
    return lines


def main():
    patch, rom_path, elf = sys.argv[1:4]
    rom = open(rom_path, "rb").read()
    new = apply_ips(rom, patch)
    for name in sys.argv[4:]:
        address, size = symbol(elf, name)
        off = (address & ~1) - 0x08000000
        before = disassemble(rom[off:off + size], address & ~1)
        after = disassemble(new[off:off + size], address & ~1)
        same = rom[off:off + size] == new[off:off + size]
        print("=== %s  %#x, %d bytes%s" % (name, address & ~1, size, "  (unchanged)" if same else ""))
        if same:
            continue
        a = ["%s  %s" % (x, y) for x, y in before]
        b = ["%s  %s" % (x, y) for x, y in after]
        for line in difflib.unified_diff(a, b, "stock", "reloaded", lineterm="", n=2):
            print(line)


main()

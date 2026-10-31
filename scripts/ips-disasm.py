#!/usr/bin/env python3
"""Disassembles a range of the *patched* game as Thumb.

Usage: ips-disasm.py PATCH.ips ROM.gba START END [--stock]

START and END are addresses (0x08......). ROM is a build of the unmodified game; the patch is
applied in memory. With --stock the range is shown unpatched. Used to read code that the
patch moved or added, which a per-function diff cannot name.
"""
import subprocess
import sys
import tempfile
import os

sys.dont_write_bytecode = True


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
        out[off:off + size] = payload
    return bytes(out)


patch, rom_path = sys.argv[1:3]
start, end = int(sys.argv[3], 16), int(sys.argv[4], 16)
rom = open(rom_path, "rb").read()
blob = rom if "--stock" in sys.argv else apply_ips(rom, patch)
chunk = blob[start - 0x08000000:end - 0x08000000]
with tempfile.NamedTemporaryFile(delete=False) as f:
    f.write(chunk)
    name = f.name
try:
    print(subprocess.run(["arm-none-eabi-objdump", "-D", "-b", "binary", "-m", "arm", "-M", "force-thumb",
                          "--adjust-vma=%#x" % start, name], capture_output=True, text=True).stdout)
finally:
    os.unlink(name)

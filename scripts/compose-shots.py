#!/usr/bin/env python3
"""compose-shots.py OUT A.png B.png ...: pastes the pictures side by side (the
cases_N.png of the smoke tests: the left wing, then the right wing)."""
import sys
from PIL import Image
pics = [Image.open(p).convert("RGB") for p in sys.argv[2:]]
out = Image.new("RGB", (sum(p.width for p in pics), max(p.height for p in pics)))
x = 0
for p in pics:
    out.paste(p, (x, 0))
    x += p.width
out.save(sys.argv[1])

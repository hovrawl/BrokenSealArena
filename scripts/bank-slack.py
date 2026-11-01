#!/usr/bin/env python3
"""Rough slack of each main-image bank (tbs-en) from the map: the last global
symbol below the next bank's start (a lower bound on use, so the slack is an
upper bound). Usage: bank-slack.py [MAP]"""
import re, sys
mp = sys.argv[1] if len(sys.argv) > 1 else '/home/nathan/alchemy/out/tbs-en/tbs-en.map'
starts = [0x08015000 - 0, 0x08077000, 0x0808a000, 0x080a1000, 0x080b0000, 0x080b6000,
          0x080c9000, 0x080f0000, 0x080f2000, 0x080f4000, 0x080f6000, 0x080f9000]
names = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13']
# bank n starts at starts[i-1]; bank 02 start comes from main.ld (not needed here)
syms = []
for line in open(mp):
    m = re.match(r'\s+0x(08[0-9a-f]{6})\s+(\w+)\s*$', line)
    if m:
        syms.append((int(m.group(1), 16), m.group(2)))
syms.sort()
bounds = starts + [0x08100000]
for i in range(len(names)):
    lo, hi = bounds[i], bounds[i + 1]
    inside = [s for s in syms if lo <= s[0] < hi]
    if inside:
        last = inside[-1]
        print('bank %s  %08x-%08x  last symbol %08x %s  (to end %#x)' % (
            names[i], lo, hi, last[0], last[1], hi - last[0]))

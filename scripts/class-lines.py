#!/usr/bin/env python3
"""Lists the class lines (series) of class_table.c: class id, requirements, count of abilities."""
import re, sys
path = sys.argv[1] if len(sys.argv) > 1 else '/home/nathan/alchemy/games/tbs/src/game/class_table.c'
text = open(path).read()
rows = re.split(r'\n    // ', text)[1:]
lines = {}
for cid, row in enumerate(rows):
    name = row.split('\n')[0]
    m = re.search(r'\.series = (\d+)', row)
    r = re.search(r'\.required = \{([^}]*)\}', row)
    req = [int(x) for x in r.group(1).split(',') if x.strip()] if r else []
    req += [0] * (4 - len(req))
    nab = len(re.findall(r'\.ability = ', row))
    if m:
        lines.setdefault(int(m.group(1)), []).append((cid, name, req, nab))
for s in sorted(lines):
    print('series', s, len(lines[s]))
    for c in lines[s]:
        print('  ', c)

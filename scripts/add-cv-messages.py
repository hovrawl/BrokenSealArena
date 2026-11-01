#!/usr/bin/env python3
"""Adds the class viewer's labels to text/en.po above the generated cups block.
Run once in WSL (patch 0044); re-run scripts/gen-cups.py afterwards."""
import re

PO = '/home/nathan/alchemy/games/tbs/text/en.po'
BEGIN = '# BEGIN GENERATED CUPS'
MSGS = [
    ('MsgArenaCvLine', 'Line'),
    ('MsgArenaCvTagNow', 'Can reach now'),
    ('MsgArenaCvTagAll', 'All classes'),
    ('MsgArenaCvDjinn', 'Djinn'),
    ('MsgArenaCvHp', 'HP'),
    ('MsgArenaCvPp', 'PP'),
    ('MsgArenaCvAttack', 'Attack'),
    ('MsgArenaCvDefense', 'Defense'),
    ('MsgArenaCvAgility', 'Agility'),
    ('MsgArenaCvLuck', 'Luck'),
    ('MsgArenaCvWard', 'Ward'),
    ('MsgArenaCvPercent', '%'),
    ('MsgArenaCvReachNow', 'Reachable now'),
    ('MsgArenaCvReachNeed', 'Needs more Djinn'),
    ('MsgArenaCvReachNever', 'Out of reach'),
    ('MsgArenaCvLv', 'Lv'),
    ('MsgArenaCvLearned', 'Learned'),
    ('MsgArenaCvNotYet', 'Not yet'),
    ('MsgArenaCvLegend', 'Red: not learned yet'),
]

text = open(PO).read()
i = text.index(BEGIN)
head = text[:i]
last = max(int(x) for x in re.findall(r'msgid "(\d+)"', head))
if 'MsgArenaCvLine' in head:
    raise SystemExit('already added')
out = ''
for k, (key, s) in enumerate(MSGS):
    out += 'msgctxt "%s"\nmsgid "%05d"\nmsgstr "%s"\n\n' % (key, last + 1 + k, s)
open(PO, 'w').write(head + out + text[i:])
print('added', len(MSGS), 'after', last)

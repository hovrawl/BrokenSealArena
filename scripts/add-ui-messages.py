#!/usr/bin/env python3
"""Adds the UI kit's labels (the touch layouts' header buttons) to text/en.po
above the generated cups block. Run once; re-run scripts/gen-cups.py after."""
import re

from alchemy_dir import ALCHEMY, GAME  # noqa: E402
PO = GAME + '/text/en.po'
BEGIN = '# BEGIN GENERATED CUPS'
MSGS = [
    ('MsgArenaUiBack', '{button_icon:2}Back'),
    ('MsgArenaUiPrevious', '{button_icon:3}'),
    ('MsgArenaUiNext', '{button_icon:4}'),
]

text = open(PO).read()
i = text.index(BEGIN)
head = text[:i]
last = max(int(x) for x in re.findall(r'msgid "(\d+)"', head))
if MSGS[0][0] in head:
    raise SystemExit('already added')
out = ''
for k, (key, s) in enumerate(MSGS):
    out += 'msgctxt "%s"\nmsgid "%05d"\nmsgstr "%s"\n\n' % (key, last + 1 + k, s)
open(PO, 'w').write(head + out + text[i:])
print('added', len(MSGS), 'after', last)

#!/usr/bin/env python3
"""Adds the mechanics NPC's messages to text/en.po, above the generated cups block.
Topic names (MsgArenaMechTopic0..5) and topic texts (MsgArenaMechText0..5), each a
set of consecutive messages. Run once, then scripts/gen-cups.py to renumber the cups.
Usage: python3 scripts/add-mech-messages.py [path to en.po]"""
import sys

from alchemy_dir import ALCHEMY, GAME  # noqa: E402
PO = sys.argv[1] if len(sys.argv) > 1 else GAME + '/text/en.po'
FIRST_ID = 10808

TOPICS = [
    "Weaknesses",
    "Element power",
    "Damage",
    "Unleash chance",
    "Status chance",
    "Physical or magic",
]

# Pages of each topic; a page is up to four lines.
TEXTS = [
    [  # weaknesses
        ["Foes resist some", "elements less than", "others. Hit the", "weakest one."],
        ["A hit that ends in", "!!! struck its weakest", "element. A hit that", "ends in a dot, its best."],
        ["A Djinni hitting a", "weakness may earn extra", "coins and exp: Power -", "Resist + 30 percent."],
        ["Foes can be weak to", "an effect, such as", "sleep. That adds 25 to", "the chance to land it."],
    ],
    [  # element power
        ["Power is how hard", "you hit with an element.", "Resist is how well you", "take a hit of it."],
        ["Each Djinni set adds", "about 5 Power and Resist", "of its element. Gear", "adds more. Cap: 255."],
        ["Power - Resist is the", "difference. Magic: each", "100 adds 50 percent.", "Physical: 25 percent."],
        ["Healing counts only", "your Power: the spell's", "power x (1 + (Power", "- 100) / 200)."],
    ],
    [  # damage
        ["Physical: (Attack -", "Defense) / 2 x the", "move's power / 10,", "then x element factor."],
        ["Magic: (move power +", "max PP / 8) x (1 + max", "PP / 1024), then x", "the element factor."],
        ["Ward: a party class", "takes 85 to 110", "percent of magic", "damage."],
        ["Summons add 2, 4, 6 or", "8 percent of max HP for", "1 to 4 Djinn, instead", "of PP bonus and Ward."],
    ],
    [  # unleash chance
        ["Each Attack may", "unleash. Swords and", "axes: 30 percent. Maces", "25. Rods and staves 35."],
        ["Gear with Criticals", "adds its percent to", "the chance. 30 plus 10", "gives 40 percent."],
        ["Delusion stops all", "unleashes. Sword, axe", "and mace ones are", "physical; rod ones magic."],
    ],
    [  # status chance
        ["Chance in percent:", "(level / 4 - Luck / 2)", "x 3 + base chance", "+ Ailment bonus."],
        ["Level is the caster's,", "Luck the target's.", "Add 25 if the target", "is weak to the effect."],
        ["Then x 100, 60 or 30", "percent by distance", "from the aim. Roll 0 to", "99: it must be below."],
        ["Luck 40+ is immune to", "Paralyze, Sleep, Charm,", "Haunt, Curse, Condemn,", "Taint and Poison."],
    ],
    [  # physical or magic
        ["Physical: Attack, sword,", "axe and mace unleashes,", "most Djinn, PP moves", "like Dragon Cloud."],
        ["Magic: Psynergy,", "summons and the unleash", "of a rod or staff."],
        ["Physical hits use your", "Attack against its", "Defense. An element also", "uses Power vs Resist."],
        ["Magic ignores Defense.", "It uses your max PP,", "element Power, its", "Resist, and Ward."],
        ["Defend halves any hit,", "Total Defense takes a", "third. Agility: turn", "order. Luck: status."],
    ],
]


def po_string(text):
    parts = text.split('\n')
    if len(parts) == 1:
        return 'msgstr "%s"' % text
    out = ['msgstr ""']
    for i, p in enumerate(parts):
        out.append('"%s%s"' % (p, '\\n' if i < len(parts) - 1 else ''))
    return '\n'.join(out)


def topic_text(pages):
    pieces = []
    for i, page in enumerate(pages):
        pieces.append('\n'.join(page) + ('{page_break}' if i < len(pages) - 1 else '{end_wait}'))
    # keep each page together in one string; page_break sits at the end of its last line
    # (the stock messages put it right after the last line, with no newline)
    out = []
    for i, page in enumerate(pages):
        lines = page[:]
        end = '{page_break}' if i < len(pages) - 1 else '{end_wait}'
        out.append('\\n'.join(lines) + end)
    return out


def main():
    src = open(PO, encoding='utf-8').read()
    if 'MsgArenaMechTopic0' in src:
        print('already added')
        return
    block = []
    n = FIRST_ID
    for i, name in enumerate(TOPICS):
        block.append('msgctxt "MsgArenaMechTopic%d"\nmsgid "%05d"\nmsgstr "%s"\n' % (i, n, name))
        n += 1
    for i, pages in enumerate(TEXTS):
        pieces = topic_text(pages)
        # pieces: one per page, lines joined by the literal backslash-n
        lines = ['msgstr ""']
        for k, piece in enumerate(pieces):
            segs = piece.split('\\n')
            for j, seg in enumerate(segs):
                last = (j == len(segs) - 1)
                lines.append('"%s%s"' % (seg, '' if last else '\\n'))
        block.append('msgctxt "MsgArenaMechText%d"\nmsgid "%05d"\n%s\n' % (i, n, '\n'.join(lines)))
        n += 1
    marker = '# BEGIN GENERATED CUPS'
    at = src.index(marker)
    src = src[:at] + '\n'.join(block) + '\n' + src[at:]
    open(PO, 'w', encoding='utf-8', newline='\n').write(src)
    print('added %d messages (%d..%d)' % (n - FIRST_ID, FIRST_ID, n - 1))


main()

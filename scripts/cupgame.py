"""Reads the game tables the cup scripts need (enemy rows, which enemies are
small, item names, Djinn names). Shared by gen-cups.py, cup-check.py and
cup-gear.py. The game tree is ~/alchemy/games/tbs unless CUP_GAME is set."""
import os
import re

GAME = os.path.expanduser(os.environ.get("CUP_GAME", "~/alchemy/games/tbs"))


def read(rel):
    with open(os.path.join(GAME, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_enemies():
    """Rows of src/game/enemy_table.c: list of dict(name, level). Index = enemy row."""
    text = read("src/game/enemy_table.c")
    body = text[text.index("gEnemy_Definitions[] = {"):]
    rows = []
    for m in re.finditer(r"^    // ([^\n]*)\n    \{(.*?)^    \},?", body, re.S | re.M):
        name, blk = m.group(1).strip(), m.group(2)
        mm = re.search(r"\.level = (-?\d+)", blk)
        rows.append(dict(name=name, level=int(mm.group(1)) if mm else 0))
    return rows


def parse_small():
    """isSmall per battle sprite index (enemy row + ENEMY_ID_FIRST = 8)."""
    text = read("src/battle/battle_sprites.c")
    body = text[text.index("gBattleSprites[] = {"):]
    blocks = re.findall(r"^    \{\n(.*?)^    \},", body, re.S | re.M)
    return [".isSmall = 1" in b for b in blocks]


ENEMY_ID_FIRST = 8


def slots(small, ids, counts):
    return sum(c * (1 if small[i + ENEMY_ID_FIRST] else 2) for i, c in zip(ids, counts))


def item_ids():
    """ITEM_* constants of include/item_ids.h -> id."""
    ids = {}
    for m in re.finditer(r"(ITEM_\w+)\s*=\s*(0x[0-9a-fA-F]+|\d+)", read("include/item_ids.h")):
        ids[m.group(1)] = int(m.group(2), 0)
    return ids

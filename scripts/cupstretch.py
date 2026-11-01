"""The stretch table: which part of the story each main cup pays its gear from.

A cup rewards the equipment the story gave between the previous cup's boss
dungeon and its own boss dungeon (docs/CUP-SPEC.md, "Gear spread").
This file is THE editable table; cup-gear.py and cup-drops.py read it (module cupstretch).

  STRETCH[cup short name] = dict(
      boss  = the story boss that closes the stretch (text, for the docs),
      scenes = scene file prefixes, in story order (a prefix matches every scene
               whose file name starts with it; "vale.c" matches exactly vale.c),
      regions = the numbers of the REGIONS list of cup-candidates.py (the encounter
               zones, hence the random mobs and so their drops, met in the stretch))

Scenes that nothing here names are listed by `cup-gear.py` under "(none)". The
Crossbone Isle (a side cup, the post-game) keeps its own scenes.
Places whose story position is a judgement call are marked GUESS.

Run:  python3 scripts/cupstretch.py     (prints the table, and the scenes left over)
"""
import os
import sys

STRETCH = [
    ("Tret", dict(
        boss="Tret (Tret Tree)",
        scenes=["vale_prologue", "vale_plaza", "vale.c", "vale_kradens", "cottage_rooms_a",
                "sol_sanctum", "goma_cave", "kolima_forest", "kolima", "log_rooms_c",
                "tree_rooms", "tret_tree"],
        regions=[1, 2, 3, 4])),
    ("Mercury", dict(
        boss="Saturos (Mercury Lighthouse)",
        scenes=["vault.c", "vault_revisit", "bilibin", "cottage_rooms_c", "mercury_lighthouse"],   # GUESS: Vault
        regions=[5, 6])),
    ("Mogall", dict(
        boss="Killer Ape (Mogall Forest)",
        scenes=["imil", "fuchin", "mogall_forest"],
        regions=[7, 8])),
    ("Altin", dict(
        boss="Hydros Statue and the Manticore",
        scenes=["xian", "altin", "alpine_crossing", "lamakan", "log_rooms_a", "log_rooms_b",
                "lacquer_rooms_b", "vale_cave", "vault_cave"],
        regions=[9, 10])),
    ("Tolbi", dict(
        boss="Kraken and the Colosso trio",
        scenes=["kalay", "stone_rooms", "tolbi", "ship_rooms", "altmiller", "colosseum"],
        regions=[11, 13, 14])),
    ("Lunpa", dict(
        boss="Toadonpa and the Lizards",
        scenes=["gondowan", "lunpa", "hammet", "west_lunpa", "rock_rooms", "stucco", "suhalla"],
        regions=[15, 16, 17])),
    ("Lighthouse", dict(
        boss="The Fusion Dragon (Venus Lighthouse)",
        scenes=["babi", "tunnel_ruins", "venus_lighthouse"],
        regions=[18, 19, 20])),
    ("Crossbone", dict(
        boss="Deadbeard (side cup, post-game)",
        scenes=["crossbone", "lalivero", "timber_rooms"],
        regions=[12])),
]

# Items whose scene says little about the story position (the world map holds
# everything buried on it): item constant -> cup short name.
ITEM_STRETCH = {
    "ITEM_TURTLE_BOOTS": "Lunpa",    # buried in the Suhalla storm; Douse brings the party down
}


def cup_of(scene):
    """The cup short name whose stretch holds the scene file (name without .c)."""
    for cup, info in STRETCH:
        for p in info["scenes"]:
            if scene.startswith(p) or scene + ".c" == p:
                return cup
    return "(none)"


def order_of(scene):
    """(cup index, position in the stretch): sorts scenes in story order."""
    for ci, (cup, info) in enumerate(STRETCH):
        for pi, p in enumerate(info["scenes"]):
            if scene.startswith(p) or scene + ".c" == p:
                return ci, pi
    return len(STRETCH), 0


if __name__ == "__main__":
    for cup, info in STRETCH:
        print("%-11s %-40s regions %s" % (cup, info["boss"], info["regions"]))
        print("            scenes: %s" % ", ".join(info["scenes"]))

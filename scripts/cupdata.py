"""The cup table: THE one place the cups are written down (docs/CUP-SPEC.md).

gen-cups.py turns this into C and messages in ~/alchemy; cup-check.py verifies it
against the game's tables (enemy ids, sprite slots). Edit here, then run
  wsl -- python3 scripts/gen-cups.py     (writes the generated files)
  wsl -- python3 scripts/cup-check.py    (must print OK)

Enemy ids are rows of src/game/enemy_table.c (the `#n` of docs/cup-candidates.md).
A round is R(targetLevel, [(enemyId, count), ...], reward=None, note="..."): the
enemies are levelled to targetLevel; a round holds at most six sprite slots (a
small enemy takes one, any other two).
boss=0/1/2 marks a round for the warning the attendant gives before it: 1 a mini-boss
(a tough opponent), 2 a boss. Left out (None) it follows the rules at the end of this file
(finish_bosses): the last round of a cup holding a story boss, and every round of the Boss
Rush, is a boss; any other round holding a story boss is a mini-boss. R(..., boss=0) forces
no warning.
Rewards on a round are given the first time the round is won (once only):
  ("djinn", element, n)   a Djinni won in a Djinn battle
  ("item", itemName)      gear from the cup's stretch of the story (GEAR below; cup-gear.py lists them)
"""

# Djinn by table index: element (0 Venus, 1 Mercury, 2 Mars, 3 Jupiter) and n.
DJINN = {
    "Venus": ["Flint", "Granite", "Quartz", "Vine", "Sap", "Ground", "Bane"],
    "Mercury": ["Fizz", "Sleet", "Mist", "Spritz", "Hail", "Tonic", "Dew"],
    "Mars": ["Forge", "Fever", "Corona", "Scorch", "Ember", "Flash", "Torch"],
    "Jupiter": ["Gust", "Breeze", "Zephyr", "Smog", "Kite", "Squall", "Luff"],
}
ELEMENTS = ["Venus", "Mercury", "Mars", "Jupiter"]


def djinn_entry(name):
    for e, el in enumerate(ELEMENTS):
        if name in DJINN[el]:
            return e * 7 + DJINN[el].index(name)
    raise KeyError(name)


class R:
    def __init__(self, level, team, reward=None, note="", boss=None):
        self.level, self.team, self.note = level, team, note
        self.boss = boss
        # one reward or a list of them; kept as a list
        if reward is None:
            reward = []
        elif isinstance(reward, tuple):
            reward = [reward]
        self.rewards = list(reward)


class Cup:
    def __init__(self, name, short, rounds, heals=True, side=False, requires=0,
                 raise_to=0, play=0, sells=(), shops="", clear_note=""):
        self.name, self.short, self.rounds = name, short, rounds
        self.heals, self.side, self.requires = heals, side, requires
        self.raise_to, self.play = raise_to, play
        self.sells = list(sells)      # Djinn the party manager sells once cleared
        self.shops = shops            # shops named in the first-clear scene
        self.clear_note = clear_note


# Djinn the manager sells before any cup is cleared (one of each element).
START_SELLS = ["Flint", "Fizz", "Fever", "Gust"]

# Item shop rows (sStockTable) the manager opens by progress (cups cleared);
# [weapons, armor, supplies]. Progress 0 is the start.
SHOP_ROWS = [
    (1, 2, 3),      # 0 Vale
    (4, 5, 6),      # 1 Vault
    (7, 8, 9),      # 2 Bilibin
    (10, 11, 12),   # 3 Imil
    (19, 20, 21),   # 4 Altin (Kolima and Xian are cheaper)
    (22, 23, 24),   # 5 Kalay
    (26, 27, 28),   # 6 Stucco (and Lunpa)
    (26, 27, 31),   # 7 Suhalla
]
CROSSBONE_ROWS = (32, 33, 34)   # Lalivero, once Crossbone Isle is cleared

CUPS = [
    # ------------------------------------------------------------------ A
    Cup("Tret Cup", "Tret", play=10, raise_to=15,
        sells=["Granite"], shops="Vault",
        rounds=[
            R(3, [(10, 2), (4, 2), (1, 1)], note="Slimes, Bats and a Vermin (Sol Sanctum)"),
            R(5, [(18, 1), (27, 2)], note="Zombie and Will Heads"),
            R(6, [(14, 1), (24, 1), (27, 1)], note="Ghost, Skeleton, Will Head (Goma)"),
            R(7, [(157, 1), (24, 1)], reward=("djinn", "Forge"), note="Forge, the Goma Cave Djinni"),
            R(8, [(30, 2), (33, 1), (36, 1)], note="Rats and a Bee (Kolima)"),
            R(9, [(39, 1), (42, 2), (45, 1)], note="Troll, Spiders, Gnome (Tret Tree)"),
            R(10, [(160, 1), (107, 1)], reward=("djinn", "Breeze"), note="Breeze, the Tret Tree Djinni"),
            R(14, [(139, 1)], note="Tret"),
        ]),
    # ------------------------------------------------------------------ B
    Cup("Mercury Cup", "Mercury", play=15, raise_to=18, requires=1,
        shops="Bilibin",
        rounds=[
            R(13, [(12, 2), (45, 2), (36, 1)], note="Bilibin cave mobs"),
            R(13, [(51, 1), (48, 1), (12, 2)], note="Grizzly, Ghoul, Oozes"),
            R(14, [(39, 1), (33, 2)], note="Troll and Rat Soldiers"),
            R(15, [(54, 3), (57, 1)], note="Cuttles and a Harpy (Mercury Lighthouse)"),
            R(15, [(153, 1), (60, 1)], reward=("djinn", "Sleet"), note="Sleet, the Lighthouse Djinni"),
            R(16, [(57, 1), (60, 1), (119, 1)], note="Harpy, Siren, Lizard Man"),
            R(17, [(119, 1), (51, 2)], note="Lizard Man and Grizzlies"),
            R(18, [(115, 1)], note="Saturos"),
        ]),
    # ------------------------------------------------------------------ C
    Cup("Mogall Cup", "Mogall", play=18, raise_to=20, requires=2,
        shops="Imil",
        rounds=[
            R(15, [(63, 2), (66, 2), (28, 1)], note="Fuchin Falls mobs"),
            R(16, [(108, 1), (25, 1), (63, 2)], note="Spirit, Bone Fighter, Moles"),
            R(16, [(161, 1), (119, 1)], reward=("djinn", "Zephyr"), note="Zephyr, the Fuchin Falls Djinni"),
            R(17, [(25, 2), (28, 2)], note="Bone Fighters and Death Heads (Mogall)"),
            R(17, [(150, 1), (108, 1)], reward=("djinn", "Quartz"), note="Quartz, the Mogall Djinni"),
            R(18, [(69, 2), (66, 2)], note="Apes and Dirges"),
            R(20, [(70, 1)], note="Killer Ape"),
        ]),
    # ------------------------------------------------------------------ D
    Cup("Altin Cup", "Altin", play=20, raise_to=25, requires=3,
        sells=["Smog", "Sap", "Kite"], shops="Kolima, Xian and Altin",
        rounds=[
            R(18, [(34, 1), (75, 1), (43, 2)], note="Altin Peak mobs"),
            R(18, [(13, 2), (55, 2), (72, 2)], note="Slime Beasts, Calamars, Grubs"),
            R(19, [(78, 1), (69, 1), (37, 2)], note="Salamander, Ape, Bees (Lamakan)"),
            R(19, [(154, 1), (130, 1)], reward=("djinn", "Spritz"), note="Spritz and the Ant Lion"),
            R(20, [(3, 2), (9, 2), (15, 1)], note="Vale Cave mobs"),
            R(21, [(40, 1), (87, 1), (52, 1)], note="Cave Troll, Gargoyle, Brown Bear (Vault Cave)"),
            R(22, [(19, 1), (15, 1), (52, 1)], note="Undead, Ghost Mage, Brown Bear"),
            R(22, [(123, 1), (122, 1)], note="Hydros Statue and a Living Statue"),
            R(24, [(81, 1)], note="Manticore"),
        ]),
    # ------------------------------------------------------------------ E
    Cup("Tolbi Cup", "Tolbi", play=25, raise_to=27, requires=4,
        sells=["Ember", "Mist"], shops="Kalay",
        rounds=[
            R(21, [(56, 3), (6, 2)], note="Man o' Wars and Rabid Bats (Tolbi ship)"),
            R(22, [(120, 1), (58, 1), (6, 1)], note="Lizard Fighter, Virago, Rabid Bat"),
            R(22, [(20, 1), (31, 1), (46, 1), (64, 1)], note="Altmiller Cave mobs"),
            R(23, [(162, 1), (93, 1)], reward=("djinn", "Squall"), note="Squall, the Altmiller Djinni"),
            R(23, [(67, 2), (73, 2), (88, 1)], note="Foul Dirges, Spear Grubs, Clay Gargoyle"),
            R(24, [(96, 1), (93, 1)], note="Cerberus and Golem"),
            R(25, [(124, 1), (126, 1), (128, 1)], note="The Colosso champions"),
            R(26, [(113, 1)], note="Kraken"),
        ]),
    # ------------------------------------------------------------------ F
    Cup("Lunpa Cup", "Lunpa", play=27, raise_to=35, requires=5,
        sells=["Scorch", "Ground", "Torch", "Tonic"], shops="Lunpa, Stucco and Suhalla",
        rounds=[
            R(25, [(35, 1), (38, 2), (84, 1)], note="Gondowan Cave mobs"),
            R(25, [(71, 1), (68, 2)], note="Dirty Ape and Vile Dirges"),
            R(26, [(23, 3)], note="Lunpa Fortress guards"),
            R(26, [(84, 1), (131, 1), (82, 1)], note="Kobold, Roach, Magicore (Suhalla Desert)"),
            R(27, [(159, 1), (74, 1)], reward=("djinn", "Flash"), note="Flash, the desert Djinni"),
            R(27, [(76, 1), (59, 1), (99, 1)], note="Orc Captain, Harridan, Stone Soldier"),
            R(28, [(156, 1), (94, 1)], reward=("djinn", "Dew"), note="Dew, the Suhalla Gate Djinni"),
            R(28, [(16, 1), (50, 1), (62, 1)], note="Horned Ghost, Cannibal Ghoul, Nightmare"),
            R(29, [(133, 1)], note="Toadonpa"),
            R(30, [(137, 1), (138, 1)], note="Storm and Tempest Lizard"),
        ]),
    # ------------------------------------------------------------------ G
    Cup("Lighthouse Cup", "Lighthouse", play=35, raise_to=50, requires=6,
        sells=["Vine", "Corona", "Hail"], shops="Suhalla",
        rounds=[
            R(33, [(47, 1), (62, 1), (85, 1)], note="Venus Lighthouse mobs"),
            R(33, [(16, 1), (94, 1), (29, 1)], note="Horned Ghost, Earth Golem, Willowisp"),
            R(34, [(32, 1), (77, 1), (29, 1)], note="Plated Rat, Orc Lord, Willowisp (Babi)"),
            R(35, [(163, 1), (26, 1)], reward=("djinn", "Luff"), note="Luff, the Babi Lighthouse Djinni"),
            R(36, [(83, 1), (89, 1), (91, 1)], note="Manticore King, Ice Gargoyle, Gryphon"),
            R(36, [(103, 1), (44, 2)], note="Chimera Mage and Recluses"),
            R(37, [(100, 1), (80, 1), (95, 1)], note="Boulder Beast, Thunder Lizard, Grand Golem"),
            R(38, [(98, 1), (95, 1)], note="Fenrir and Grand Golem"),
            R(40, [(118, 1), (116, 1)], note="Menardi and Saturos"),
            R(41, [(140, 1)], note="The Fusion Dragon"),
        ]),
    # ------------------------------------------------------------ side: Boss Rush
    Cup("Boss Rush", "Boss Rush", side=True, heals=False, requires=7,
        rounds=[
            R(14, [(77, 1), (121, 1)], note="Orc Lord and Lizard King"),
            R(22, [(81, 1), (102, 1)], note="Manticore and Chimera"),
            R(30, [(138, 1), (97, 1)], note="Tempest Lizard and Cerberus"),
            R(36, [(115, 1), (118, 1)], note="Saturos and Menardi"),
            R(41, [(141, 1), (123, 1)], note="Deadbeard and the Hydros Statue"),
            R(45, [(140, 1)], note="The Fusion Dragon"),
        ]),
    # --------------------------------------------------------- side: Crossbone Isle
    Cup("Crossbone Isle", "Crossbone", side=True, requires=7,
        sells=["Bane"], shops="Lalivero",
        rounds=[
            R(23, [(86, 1), (58, 2)], note="Hobgoblin and Viragos (first guards)"),
            R(23, [(53, 2), (61, 1)], note="Savage Bears and a Succubus"),
            R(24, [(17, 1), (49, 2)], note="Lich Ghost and Fiendish Ghouls"),
            R(25, [(90, 2)], note="Gryphons"),
            R(28, [(121, 1), (59, 1), (99, 2)], note="Lizard King, Harridan, Stone Soldiers (last guards)"),
            R(28, [(102, 2)], note="Chimeras"),
            R(28, [(79, 2)], note="Earth Lizards"),
            R(32, [(134, 1), (80, 2)], note="Poison Toad and Thunder Lizards"),
            R(33, [(97, 2)], note="Hell Hounds"),
            R(43, [(141, 1)], note="Deadbeard"),
        ]),
]

MAIN_COUNT = sum(1 for c in CUPS if not c.side)

# Enemy ids of the story bosses (rows of the enemy table): Tret, Saturos (two rows),
# Killer Ape, Hydros, Manticore, Kraken, Toadonpa, Storm and Tempest Lizard, Menardi,
# Fusion Dragon, Deadbeard and the Colosso trio.
STORY_BOSSES = {139, 115, 116, 70, 123, 81, 113, 133, 137, 138, 118, 140, 141,
                124, 125, 126, 127, 128, 129}


def finish_bosses():
    """Fills in R.boss where the cup table left it out (see the top of this file):
    a main cup's last round is a boss, a Boss Rush round is a boss, any other round with a
    story boss is a mini-boss."""
    for ci, cup in enumerate(CUPS):
        last = len(cup.rounds) - 1
        for ri, rd in enumerate(cup.rounds):
            if rd.boss is not None:
                continue
            has_boss = any(e in STORY_BOSSES for e, _ in rd.team)
            if cup.name == "Boss Rush":
                rd.boss = 2
            elif ri == last and (not cup.side or has_boss):
                rd.boss = 2
            elif has_boss:
                rd.boss = 1
            else:
                rd.boss = 0


finish_bosses()

# Gear for the first win of a round: {cup short name: {round number: [ITEM_*]}}. Each cup pays
# the equipment of its whole stretch of the story (the previous cup's boss dungeon up to its
# own: scripts/cupstretch.py), chests, gifts and the rare drops of the stretch's mobs
# (`cup-gear.py --equip` and `cup-drops.py` list them). Equipment only. Spread over the rounds
# in story order, at most two per round; within a type each piece is dearer than the one
# before (the Golden Rule of docs/RELOADED-DESIGN.md). Left out: the Colosso prizes (Iron
# Shield, Padded Gloves, Chain Mail, Cotton Shirt, Claymore, Hunter's Sword: weaker than shop
# stock by then) and Bandit's Sword (a 320 coin weapon).
GEAR = {
    "Tret": {5: ["ITEM_FUR_COAT"], 6: ["ITEM_HEALING_RING"]},
    "Mercury": {3: ["ITEM_ELVEN_RAPIER"], 6: ["ITEM_PSYNERGY_ARMOR"]},
    "Mogall": {2: ["ITEM_UNICORN_RING"], 3: ["ITEM_ARCTIC_BLADE"], 5: ["ITEM_ELVEN_SHIRT"]},
    "Altin": {3: ["ITEM_VULCAN_AXE"], 6: ["ITEM_VAMBRACE"]},          # Lamakan; Vault Cave
    "Tolbi": {2: ["ITEM_SPIRIT_GLOVES"],                                # Kalay
              6: ["ITEM_PROPHETS_HAT"]},                                # drop: Cerberus (Altmiller)
    "Lunpa": {2: ["ITEM_WATER_JACKET"],                                 # Hammet Palace
              3: ["ITEM_MYTHRIL_CIRCLET"],                              # Lunpa Fortress
              4: ["ITEM_VIRTUOUS_ARMLET", "ITEM_AURA_GLOVES"],          # Suhalla Desert; drop: Magicore
              6: ["ITEM_TURTLE_BOOTS"]},                                # buried in the storm
    "Lighthouse": {1: ["ITEM_LURE_CAP"],                                # Babi Palace
                   2: ["ITEM_ORACLES_ROBE"],                            # Tunnel Ruins
                   3: ["ITEM_LUCKY_CAP"],                               # Venus Lighthouse
                   5: ["ITEM_SPIKED_ARMOR", "ITEM_THUNDER_CROWN"],      # drop: Chimera Mage
                   6: ["ITEM_FEATHERED_ROBE", "ITEM_ASURAS_ARMOR"],     # drop: Wild Gryphon; Tunnel Ruins
                   7: ["ITEM_DRAGON_SCALES", "ITEM_BLESSED_MACE"],      # drop: Thunder Lizard
                   8: ["ITEM_ZODIAC_WAND"],                             # drop: Grand Golem
                   9: ["ITEM_GAIA_BLADE"]},
    "Crossbone": {1: ["ITEM_WARRIORS_HELM"], 2: ["ITEM_FAIRY_RING"], 3: ["ITEM_CLERICS_RING"],
                  4: ["ITEM_MYSTERY_BLADE"], 5: ["ITEM_STORM_GEAR"], 6: ["ITEM_NINJA_GARB"],
                  7: ["ITEM_WICKED_MACE"], 8: ["ITEM_DEMON_MAIL"], 9: ["ITEM_MURAMASA"],
                  10: ["ITEM_DEMON_AXE"]},
}
for _cup in CUPS:
    for _round, _items in GEAR.get(_cup.short, {}).items():
        _cup.rounds[_round - 1].rewards += [("item", i) for i in _items]

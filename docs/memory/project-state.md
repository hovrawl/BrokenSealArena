# Project state (update when it changes)

As of the 7-patch layered series on upstream `0033cb64ef` (re-sliced from the
original 13 chronological patches, kept in this repo's history at commit `01a3234`; our code
now lives in our own files, see `docs/CHANGES.md`):

**Built and smoke-tested:** New Game boots into the arena (level 30 Isaac, Garet,
Mia, Ivan, 1500 coins); the attendant's Solo/Multiplayer and tournament menus
(one tournament: the 12-rung Monster Gauntlet of mixed teams); the party manager
(Characters stats, Djinn, Psynergy, item shops) with shop-style counters, animated
Djinni figures, a status panel; coins won per battle; saving through the Pause
menu and loading with Continue.

**Open ideas:** more tournaments (needs a way for `ArenaLadder_Select` to know
which), saving the ladder rung, balance pass (round 3 spikes with a boss), CPU
teams as real player-style units (Route B), multiplayer, other editions, CHILD
sprites for characters beyond the four, The Lost Age port.

**Not done:** other language editions; the party is fixed at four characters.

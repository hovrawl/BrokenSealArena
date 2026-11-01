# Headless smoke tests

A small driver on libmgba runs the built ROM with no window, presses buttons from
a script, and writes screenshots (PNG) and memory reads. It is about 100 times
faster than real time (a 1,400-frame boot takes under a second), so a change can
be looked at straight after a build.

## Why not mGBA's own debugger

The Windows mGBA 0.10.5 in `C:\Dev\Tools` has no `--script` flag (that arrives in
0.11; scripts can only be loaded from the Qt window's Tools menu) and was built
without the command-line debugger (its `-d` flag is absent). Its GDB server
(`-g`) can read memory and step, but cannot press buttons or capture the screen.
`libmgba` can do all of that, and Alchemy's own Devtools render GIFs the same
way. The driver is `scripts/smoke/smoke.c`.

## Use

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke.ps1 pause.txt -Fresh
```

- Runs `scripts/smoke/<script>` against `~/alchemy/out/tbs-en/tbs-en.gba` in WSL
  (build first with `build.ps1`, which leaves that file in place).
- Screenshots land in `build\smoke\shots`, with `sheet.png`, all of them on one
  page, which is the cheapest way to look at a run.
- `-Fresh` deletes the test cartridge save (`/tmp/smokesave` in WSL, not your
  emulator's `.sav`); without it a run keeps the last run's save.

One-time setup (WSL): `sudo apt install libmgba-dev python3-pil` (libpng-dev and
a C compiler are already there for the build).

## Script commands (one a line, `#` comments)

| Command | Does |
|---|---|
| `wait N` | run N frames |
| `press KEYS N` | hold KEYS for N frames, then release |
| `tap KEYS` | press for 4 frames, then 20 frames of nothing |
| `mash KEYS N` | tap N times (steps through dialogue and battle menus) |
| `include FILE` | run another script from this folder first |
| `shot /tmp/shots/NAME.png` | save the screen, 240 by 160 scaled by 3 |
| `peek HEXADDR N` | print N (1, 2 or 4) bytes at an address |
| `poke HEXADDR N VALUE` | write VALUE (decimal) as N bytes |
| `save FILE` / `load FILE` | savestate |
| `reset` | restart the console; the cartridge save is kept (to test Continue) |

Keys: `A B`, `S` select, `T` start, `U D L R` the D-pad, `l r` the shoulders.
Combine them: `press AD 3`.

## Scripts here

Prefixes (use them with `include`):
- `to_lobby.txt`: New Game and the greeter's introduction (six pages); ends with control of Isaac.
- `onboarding.txt`: the introduction page by page, the flag peeked (0x0200013C: 0 then 1),
  then her stock welcome. `onboarding_seen.txt`: the flag poked to 1, stock welcome at once.
- `to_manager.txt`: walk to the party manager (right counter) and talk to him.
- `to_solo.txt`: talk to the attendant (left counter), choose Solo and the
  Monster Gauntlet.

Tests (each ends in shots; `build\smoke\shots\sheet.png` shows them all):
- `attendant.txt`: Solo/Multiplayer, tournaments, her last line.
- `manager.txt`: Characters: status panel, the stat counter, a purchase.
- `djinn.txt`, `psynergy.txt`: picker panel, counter, a purchase, paging.
- `items.txt`: the shop choice and the real Xian shop.
- `battle.txt`: walk into the circle; the first team appears.
- `win.txt`: fight the Gauntlet by mashing A; shows each step and the
  "Victory! You won 200 coins." message.
- `give_up.txt`: talk to the attendant mid-series: the give-up question, No
  ("Good luck!"), then Yes (the series ends) and the normal menu is back.
- `round.txt`: win round 1; the next-round line, and the player outside the circle
  with control.
- `clear.txt`: win with the win count poked to 11 mid-battle (`poke 0x020004EA 2
  11`: `gMainRoutineWork` 0x02000240 + 0x2a4 + 6, the streak tally), so the win is
  the 12th: the cleared line and the end-of-series line.
- `lose.txt`: the win count poked to 11 before the circle, so the fight is round 12
  and mashing A loses; shots every few presses to catch the loss line (more A
  presses open the field menu, which shows the party restored).
- `rungs.txt`: the first frame of every Gauntlet rung. It reaches the series once,
  saves a state, then for each rung loads it, pokes the win count and walks into the
  circle (all twelve teams render, within six sprite slots).
- `resume.txt`: save mid-series through the Pause menu, `reset`, choose Continue,
  `peek` the win count (0x020004EA) and the series flag (0x0200006E, 8 when set),
  walk up and talk: "Round 6 of 12. Do you want to give up?". The title needs
  Continue chosen with D, A, A, A (with waits); Isaac starts at the door with no
  greeter walk-in, so the walk to the attendant differs from `to_solo.txt`.
- `tournaments.txt`: the tournament menu (two icons), choosing the Boss Rush, the
  give-up question saying "of 6", and the tournament byte (`peek 0x0200013F`).
  `to_rush.txt` is the prefix that picks it.
- `rungs_rush.txt`: the first frame of each of the six Boss Rush rungs.
- `rush_round.txt` / `heal_round.txt`: win round 1 and walk into the next fight; the
  HUD shows the HP carried over (Boss Rush) or full HP (Gauntlet).
- `rush_manager.txt`: after a Boss Rush win, leave the manager with B and read
  Garet's HP in his Characters panel (it stays hurt; the exit does not heal).
- `rush_clear.txt`: clear the Boss Rush (win count poked to 5): 700 coins, the
  cleared line, "You won 6 battles."
- `resume_rush.txt`: save in the Boss Rush, `reset`, Continue: "Round 4 of 6.", and
  the tournament byte is kept.
  Boss Rush round 1 cannot be won by pressing A (bosses), so the scripts that need
  a win start the battle as the Gauntlet's easy first team (poke the tournament byte
  to 0), then poke it back to 1 once the battle is under way.
- `link.c` + `link.sh`: a **two-console** driver (two ROM instances on libmgba's
  lockstep link; `link.sh SCRIPT0 SCRIPT1`, shots named `p0_*` and `p1_*`).
  `link_att_*.txt` brings the link up at the attendant; `link_battle_*.txt` runs the
  whole stock Multiplayer flow to a linked battle. See `docs/MULTIPLAYER.md`. It must
  be built with `-DENABLE_SCRIPTING` (`link.sh` does). `link-run.sh NAME` runs
  `link_NAME_0/1.txt` and keeps the log and shots under `build/smoke/link/NAME/`; set
  `ROM1=` to a second ROM to link two builds (`link_mm_*` waits for an opponent,
  `link_recover_*` is five turns with Djinn, a Summon and the recovery tables).
  **Turns:** a turn's messages wait for a button, so step them with `tap B` (30 taps of
  100 frames); B does nothing at the command menu, so extra taps are harmless, unlike A.
  A unit that dies changes the order of the command menus, so keep the scripts short.
- `rules_turn.txt`: fight a few rounds and `peek` `BattleWork.arenaTurn` (0x47 into the
  battle work, which `gBattleWork`, 0x03001e74, points to): 0 in the first turn, 1 after it.
- `pause.txt`, `save.txt`: the Pause menu and Save your quest.
- `boot.txt`, `walk.txt`: calibration runs.
## Checking the Reloaded data port (no emulator)

These read the built ROM, an unmodified upstream build (`~/alchemy-stock`) and the
git-ignored `reloaded/` folder; they print counts and differences, never the numbers
themselves, and write nothing in the repository. Run them in WSL with `python3` (they call
`arm-none-eabi-nm`); `workbook-check.py` also runs on Windows.

- `scripts/port-reloaded-tables.py --check` renders every row of each stock table with the
  converter's formatter and compares it with our C source (must say 0 mismatches), then says
  how many rows the patch changes. Without `--check` it rewrites the source (the port itself;
  run once on pristine tables).
- `scripts/table-check.py` compares each table of our built ROM with the stock ROM with the
  IPS applied in memory, record by record. After the port it must say 0 records differ for
  every table (`--ignore-reserved` leaves out the enemy bytes 30 to 39 the port skips).
- `scripts/ips-text-diff.py ... --ours OURROM OURELF` decodes the message archive of the
  stock, patched and our ROMs (the decoder reads all 10,723 stock messages back identically to
  `en.po`), lists the messages the patch changes and checks ours match the patched stock.
- `scripts/workbook-check.py` spot-checks our tables against the authors' Excel documentation:
  spell PP and power by name, weapon attack and price, armour defense and price, class
  multipliers. The workbooks also document The Lost Age, so a few names (Masamune, Dragon
  Shield, the Gale family) are listed that differ for that reason; renamed classes are matched
  by their numbers.
- `scripts/levelup-check.py - OURROM OURELF 99` prints the base stats at a level from OUR
  curves with the deterministic rule: level 99 equals the workbook's "Lv99 Character Stats".
  `scripts/smoke/stats.txt` prints the in-game base stats; at level 50 they match
  `levelup-check.py ... 50`.

## Tips

- New Game starts a fresh arena with the greeter talking at once; each `tap A`
  moves one page. A stray A beside a person starts their talk, so tap, wait and
  shoot, then decide the next key from the picture.
- Addresses for `peek`: EWRAM variables are in the build's map
  (`~/alchemy/out/tbs-en/tbs-en.map`).
- The ROM is copied to the save directory first, so the run never touches
  `build\tbs-en.gba` or your own saves.

## Cup scripts (patch 0027)

The Gauntlet and Boss Rush scripts (`clear`, `rungs`, `rungs_rush`, `tournaments`,
`to_rush`, `rush_*`, `resume_rush`) were removed. `to_solo.txt` now starts the first cup.
- `cup_menu.txt`: nothing cleared: Solo goes to "Enter the Tret Cup?".
- `cup_menu2.txt`, `cup_menu3.txt`: progress poked (0x0200013E) to 6 and 7: Next/Replay,
  Early/Later groups, rows of four and two, Replay/Side cups, the side row.
- `cup_clear.txt`: first clear of the Tret Cup (win count poked to 7 mid-battle): victory,
  the unlock scene, level 15.
- `cup_reward_item.txt`, `cup_reward_djinn.txt`: a gear round (Power Bread) and the Forge round.
- `cup_reward_item2.txt`: the Lighthouse Cup (cup byte poked to 6), round 6: two gear messages.
- `cup_rungs.txt`: the first frame of all 76 rounds of the 9 cups (generated; cup byte 0x0200013F).
Poke map: cup 0x0200013F, progress 0x0200013E, side bits 0x0200013D, streak 0x020004EA.

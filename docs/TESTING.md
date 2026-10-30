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
- `to_lobby.txt`: New Game and the greeter's lines; ends with control of Isaac.
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
  be built with `-DENABLE_SCRIPTING` (`link.sh` does).
- `pause.txt`, `save.txt`: the Pause menu and Save your quest.
- `boot.txt`, `walk.txt`: calibration runs.
## Tips

- New Game starts a fresh arena with the greeter talking at once; each `tap A`
  moves one page. A stray A beside a person starts their talk, so tap, wait and
  shoot, then decide the next key from the picture.
- Addresses for `peek`: EWRAM variables are in the build's map
  (`~/alchemy/out/tbs-en/tbs-en.map`).
- The ROM is copied to the save directory first, so the run never touches
  `build\tbs-en.gba` or your own saves.

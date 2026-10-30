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

# Controls

How to play the arena on each build. The GBA ROM uses the console's buttons
(or your emulator's mapping of them); everything else here is the desktop
build (`build\native\tbs-native.exe`, `.\build.ps1 -Native`).

## Keyboard (desktop build)

| Key | GBA button | What it does in the arena |
|---|---|---|
| Arrow keys | D-pad | walk; move the cursor in menus |
| X | A | talk, check, confirm |
| Z | B | cancel, back; hold to hurry text |
| Enter | Start | the Pause menu (save, sleep, settings) |
| Backspace or right Shift | Select | the field menu (Psynergy, Item, Status) |
| A | L | previous page, previous character, the L shortcut |
| S | R | next page, next character, the R shortcut |
| Tab (hold) | | fast-forward: runs without the frame limit |
| Escape | | quit |

The keys are fixed for now (there is no remapping screen yet).

## Gamepad (desktop build)

Laid out as on a GBA: the bottom face button is A, the right one B, the
shoulders L and R, Back is Select and Start is Start. The D-pad or the left
stick walks.

## Mouse and touch (desktop build)

SDL feeds a touch screen to the game as the mouse, so the two work the same:

- **In the field (the lobby):**
  - **Drag to walk.** Put a finger (or the mouse button) down anywhere and drag:
    the leader walks the way you drag, in any direction, like a stick centred
    where you pressed. Drag further (about 28 pixels of the game's screen) to
    run. The centre follows your finger, so turning round takes a short move.
  - **Tap a person next to you** to face and talk to them: the leader turns to
    them and they answer, from any side, even across a counter (up to about
    three steps away). A tap on someone further off does nothing.
  - **Tap near the middle of the screen** (on the floor, not a person) to check
    whatever is in front of the leader (A), or open the field menu when
    nothing is there.
  - **Tap anywhere** to move a message on; keep a finger down to hurry its text.
- **In menus:** tap a choice to select it, tap it again to confirm. This works
  on the party manager and its shops, the attendant's and manager's icon rows,
  the Pause menu, the class viewer, the mechanics teacher, the field menu's
  party row and Psynergy list, and in battle on the command row, the Psynergy,
  Djinn, Item and Summon lists and the targets. Page arrows take taps too.
- **Back:** the **Back** button at the top right (shops, class viewer,
  mechanics) or beside a battle menu presses B. The **right mouse button** is
  always B.
- **In battle, double tap and hold** to speed through messages, like holding
  B: tap, then put the finger straight back down near the same spot and keep
  it there. B is held until you lift it. A quick double tap (both taps short)
  is still two taps, so tap to select then tap to confirm works as before.
- **Tap the background to go back**, like a phone's back gesture: a tap on the
  room or the battlefield, outside every window, icon and person, presses B.
  It closes the manager's and attendant's icon rows, the field menu and the
  Pause menu, and takes a battle list back to the command row. A tap within a
  few pixels of a window or an icon does nothing, so a near miss never backs
  out.

A drag never counts as a tap: if your finger slides more than a few pixels, the
release does nothing, so you can change your mind by sliding off.

## Command line (desktop build)

| Option | Environment | What it does |
|---|---|---|
| `--ui touch` / `--ui classic` | `TBS_UI` | the arena's own screens in their touch layout (full width, header buttons, bigger rows, Back buttons in battle; the default) or as on the GBA |
| `--ui-size 16` / `24` | `TBS_UI_SIZE` | row height of the touch layout's lists (default 24) |
| `--width 240` / `256` / `288` (or `3:2`, `16:10`, `16:9`) | `TBS_WIDTH` | the screen's width in pixels; 160 lines always |
| `--scale N` | | window size: N times the game's pixels (default 4); the window can be resized |
| `--fullscreen` | | start full screen |
| `--screen classviewer` / `mechanics` | `TBS_SCREEN` | open that screen straight from the lobby (for testing) |
| | `TBS_SAVE` | the save file (default `tbs-native.sav` in the working directory) |

Taps in the menus work in both layouts; the battle menus' taps and Back buttons
are part of the touch layout only. Drag to walk and tap to talk work in both.

Example: `build\native\tbs-native.exe --width 16:9 --ui touch --scale 5`.

## Not yet

- The field has no on-screen Start or Select, so without a key or pad you
  cannot open the Pause menu or the field menu yet.
- In battle the Djinn list's Back button is hidden under its stat preview;
  right-click (or Z) still goes back.
- The item commands (Use, Equip, Details / Give, Remove, Drop) keep the GBA's
  8-pixel rows, small for a finger (their taps reach about 16 pixels).
- A tap dead centre does not close the field menu: the leader stands there,
  and a person is not background. Tap the floor beside him instead.

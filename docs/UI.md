# Interface rules

How we build screens, windows and menus for the hack, so a new one looks like it
shipped with the game the first time. Read this before designing or writing any
interface. It joins three sources: what we learned building the arena's screens
(`docs/CHANGES.md`, `docs/GOTCHAS.md`), the upstream interface guides
([overview](https://alchemy.pascalpixel.com/tbs/interface),
[windows](https://alchemy.pascalpixel.com/tbs/interface/window),
[menus](https://alchemy.pascalpixel.com/tbs/interface/menu),
[shops](https://alchemy.pascalpixel.com/tbs/interface/shop)), and the source.

## 1. Design intents

1. **It must look native.** A player should not be able to tell which screens are
   ours. The shops are the model: the same windows, borders, icons, hand cursor,
   price tags, font and sounds.
2. **Reuse first, invent last.** Our first from-scratch screens had the wrong
   font, did not wrap and looked wrong everywhere; every one that got good did so
   by copying an existing screen's parts. New drawing code is the exception and
   needs a reason written down.
3. **One way to do each thing.** A choice is an icon row with a prompt. A list of
   things to buy is a counter. A yes/no is the game's yes/no. A line of speech is
   a message. If two of our screens do the same job differently, one is wrong.
4. **Words are messages.** All text the player reads is a game message in
   `text/en.po`, so it draws in the game's font and wraps and pages as the
   game's text does.
5. **Look at it before saying it works.** Every state of every screen gets a
   screenshot from the smoke suite, checked against the stock screen it copies.

## 2. How to build a new interface

Do these in order; skip none. The point is to settle the look on paper, where a
change costs nothing, before it costs a build.

1. **Name the job** in one sentence ("ask whether to give up the series").
2. **Find the closest existing screen** in the catalogue (section 5) or in the
   stock game. If the job is "choose one of a few", "buy from a list", "pick a
   party member", "ask yes or no" or "say a line", it already exists; use it.
3. **Read that screen's source and the matching upstream guide.** Note which
   functions it calls and the coordinates of every window.
4. **Fill in the spec** (section 7) and have it reviewed before code. This is
   where "text is the wrong font" and "it does not wrap" are caught.
5. **Build by copying the reference's calls**, changing as little as possible:
   same window sizes and positions, same cursor and sound calls, new messages.
6. **Write the smoke script** that reaches every state and takes a shot of each,
   including a stock screen to compare against.
7. **Check the list in section 6**, then look at the sheet. Only then show it.
8. **Record it in the catalogue** with what it reuses.

## 3. Rules

### Text
- Every line the player reads is a message (`MsgArena*`, added at the end of
  `en.po`; keys must be contiguous from 0). A prompt is opened with
  `Message_OpenWindow(prompt, 5, 0, 0x22)`, as `Shop_ShowKeeperMessage` does.
  Wait for it with `Message_AllTyped`; clear it with
  `Message_CloseFinishedWindows`.
- **Labels, names and numbers are drawn as window tiles**:
  `Text_DrawMessageAsTiles`, `Text_Draw*InWindow`, `Text_DrawNumberInWindow`. Never
  the canvas calls `Text_DrawString` and `Text_DrawNumber`: they use a different,
  monospaced font and ignore `Window_ClearInteriorTiles`.
- **Messages are laid out by hand.** The stock messages break their lines with
  `\n` in the `.po` (about 20 characters or fewer a line, for example "Not bad!
  Would you" / "like to fight" / "the next monster?"), start a new page with
  `{page_break}`, and have at most four lines a page; the window is sized to the
  text. Write ours the same way, and compare the line length with a stock message.
  A tile label is one line and never wraps. Anything long is a message.
- **End codes matter.** A prompt that leads into a menu or a Yes/No ends with
  `{end_now}` (the window stays for the choice). A line the player must read ends
  with `{end_wait}` (it waits for a button). Copy the stock message nearest in
  purpose.
- **Dynamic text is a message with a blank**, filled by `MessageArgument_Push`
  before it is drawn (eight blanks at most; numbers `MESSAGE_ARGUMENT_NUMBER`,
  names `{argument_actor_name:1}`, a plural with `battle{plural_suffix}`).
- **Clear before every redraw** with `Window_ClearInteriorTiles`, or the old text
  shows through wherever the new text is shorter. The text-tile pool is small
  (128 tiles, 256 with `Text_UseExtraTiles`); a screen that redraws long lists
  needs to release tiles (upstream names `Window_ClearTextTilesInRect`; check
  which one the screen needs).
- **Tile text snaps to an 8-pixel row.** A name drawn at y + 4 lands at y. With
  16-pixel rows put the name at y + 8 and the icon at y + 4, as the Status screen
  does.
- There is no cursor glyph and no up-arrow glyph in the message font. Use the
  hand sprite for the cursor; say "Up" in words.

### Windows
- The grid is 8-pixel tiles, 30 across and 20 down. A window is 2 to 30 tiles on
  a side. All windows share one layer.
- Open with `WINDOW_FLAG_INSTANT` (the menus do). `Window_Create` waits, so the
  caller must be able to wait (a function that runs in the frame loop).
- At most 8 windows are open at once, and a closing window keeps its slot for four
  frames. Close every window you opened, on every exit path, including B.
- Only one text-canvas window can show at a time, and we do not use canvas
  windows. Sprites carried by windows are limited to 64 across all windows.
- Use the standard slots (section 4), not new coordinates, unless the reference
  screen has them.

### Icons and sprites
- Icon rows: **at most four** icons. Five or more left the prompt's window empty
  (the video-memory cache is shared by icons and message text).
- The command icons are fixed art with fixed names. Draw our label from our own
  messages (`IconMenu_Center` takes consecutive messages from a base, label =
  base + position). Some icons do not suit a label, and some do not draw in the
  arena (`COMMAND_ICON_EQUIP` does not; `COMMAND_ICON_ATTACK` does): try the icon
  in the smoke script before choosing it.
- Item, Psynergy and command icons come from `window/icons.c`. A Psynergy icon is
  `WindowSprite_CreateFromResource(ICON_KIND_ABILITY, id, ...)` with sentinel 252.
- A creature in a menu is an actor `Sprite`, not a window icon. It must be placed
  every frame (`Render_ApplyProjectedPlacement`) or it does not draw.

### Cursor, input and sound
- The cursor is the hand: `MenuCursor_Place(window, x, y)` and
  `MenuCursor_SetPositionImmediate`. A tile `>` is wrong.
- Keys: A confirms, B backs out one step (and leaves from the first), Left/Right
  move along a row, Up/Down move a row or page, L/R page. Use `gKeysPressed` for
  confirm and cancel and `gKeysRepeat` for movement.
- Sounds: `SE_MENU_CONFIRM`, `SE_MENU_CANCEL`, `SE_MENU_CURSOR_MOVE`, as the shops.
- **Wait for held keys to be released when a screen opens**
  (`while (gKeysHeld != 0) wait(1);`), or the key that opened it also acts in it.
- Not decided: stock menus close from any depth on Start
  (`FLAG_MENU_START_PRESSED`). Ours do not handle Start.

### Where the code lives
- A scene overlay (the arena, the file screen) cannot reach main-image private
  state. A screen that needs it (the shop work block, the icon menu) lives in the
  main image beside that state, with a far-call export and an import row.
- Overlays have no string literals or static data of their own: use global
  `const` arrays.
- `gMenuWork` is one shared block (the shop's work and the field menu's work are
  the same bytes). Do not call a menu-bank function that reads the other layout;
  copy its drawing instead.
- Bank space is limited; check the map before adding to a main-image bank.

## 4. Standard layouts we have already used

Positions are tile coordinates (x, y, width, height) unless a pixel offset is
named. Copy these.

| Part | Window / call | Used by |
|---|---|---|
| Prompt line | `Message_OpenWindow(prompt, 5, 0, 0x22)`: a message window across the top | every icon menu, the counters |
| Icon row | `IconMenu_Open`, `IconMenu_AddIcon` (at most 4), `IconMenu_Center(17, 13, labelBase)`, `IconMenu_Run(0)`, `IconMenu_Close` | attendant, manager, shop choice (`ArenaMenu_IconChoose`) |
| Party strip | (0, 14, 13, 3); hand at x = member * 24 - 12 | member picker (`ItemPicker_ChooseMember`) |
| Info panel | (0, 0, 30, 11); first pixel at screen (8, 8); 224 by 64 pixels inside | status, Djinn and Psynergy panels |
| Coins window | `Shop_DrawMoney`, top right | counters |
| Price window | (0, 8, `SHOP_PRICE_WIDTH`, 4) | counters |
| Stock row | (0, 12, 30, 4); seven a page, 32 pixels apart; hand at x = slot * 32 - 8 | counters |
| Description | (0, 17, 30, 3), `Shop_DrawMessage` | counters |
| Price tag | `Shop_CreatePriceSprite` under each entry | counters |
| Yes/No | the game's own: `Event_AskYesNoWithActorAnimation(actor, 0)` in a scene event, `Shop_AskYesNo` in a counter, `YesNoMenu_Run` elsewhere | stock attendant; the give-up question |
| A person speaks | `Event_SetMessageId` then `FieldMessage_ShowAtActor(actor, 0)` | the win message, the attendant's lines |
| A counter | `Shop_Run(row, keeper)` opens the real shop | the item shops |

## 5. Catalogue of finished interfaces

What each is made of, so a new one can start from the nearest.

| Interface | Reuses | Code |
|---|---|---|
| Attendant: Solo or Multiplayer, then the tournament | prompt + icon row (Fight, Cable; Battle) | `ArenaMenu_AttendantMode` (`scene/arena_menu.c`) |
| Party manager: Characters, Djinn, Psynergy, Items | prompt + icon row of four; party strip; counters | `BattleArena_PartyManager` |
| Item shops: Weapons, Armor, Supplies | icon row of three, then the real shop | `Shop_Run` on Xian's stock rows 16 to 18 |
| Member picker | the shop's party strip, `ItemPicker_Run`'s windows | `ItemPicker_ChooseMember(mode)` (`shop/shop/arena_shop.c`) |
| Status panel (Characters) | a copy of the Status screen's top rows (`ItemMenu_DrawMemberStatus`, `StatusScreen_ShowMemberStatus`'s portrait) | picker mode 3 |
| Djinn and Psynergy panels | 30 by 11 panel; ability icons; animated element figures | picker modes 1 and 2 |
| Stat, Djinn and Psynergy counters | `Shop_SelectBuy`'s whole layout | `ArenaShop_Run(kind, unit)` |
| Win report | the attendant speaking a message with the coins as a blank | `ArenaMenu_ShowWin` |
| Saving | the Pause menu and its own file list and messages | stock `PauseMenu_Run`, `Save_ToChosenFile` |

## 6. Review checklist (before anyone looks at it)

- [ ] Every string the player reads is a message; nothing uses the canvas calls.
- [ ] Long text is a message, not a tile label; its lines are hand-broken at stock
      length and it ends with the right code (`{end_now}` or `{end_wait}`).
- [ ] Every redraw clears first; no old text shows through. Check by going to a
      shorter entry and back.
- [ ] Windows, icons and the cursor sit in the standard slots; alignment is the
      same as the stock screen it copies (compare the two shots side by side).
- [ ] Icon rows have four or fewer icons, and each icon draws in the arena.
- [ ] A confirms, B backs out, the held key that opened the screen does nothing.
- [ ] Every exit path closes every window it opened (no stuck window after B).
- [ ] Sounds match the shops (confirm, cancel, cursor).
- [ ] Every state has a shot in the smoke sheet, including the empty and the
      full case (no Djinn, a full page, a maxed stat, not enough coins).
- [ ] The new messages are at the end of `en.po` and the build is clean.
- [ ] The catalogue above is updated.

## 7. Spec template

Fill this in and agree it before writing code. One block per screen.

```
Screen:        (name)
Job:           (one sentence)
Closest model: (a screen from section 5 or a stock screen, with its source file)
Opened from:   (the person, trigger or menu)
States:        (every state, in order, including empty, full, error)
Windows:       (each window: x, y, w, h, what is drawn, and the call that draws it)
Text:          (each message: key, wording, blanks; which are labels)
Icons/sprites: (which, how many; checked to draw in the arena?)
Input:         (A, B, directions, L/R, Start)
Sounds:        (confirm, cancel, move, anything special)
Lives in:      (main image or overlay; far-call and import rows needed)
Shots:         (the smoke script and the shots it must produce)
Open questions:(what needs a decision)
```

## 8. Interfaces still to design

These come from the series decisions in `docs/ROADMAP.md`. Each needs a spec
(section 7) and review before it is built. Proposed models in brackets.

| Interface | Proposed model | Open |
|---|---|---|
| Attendant while a series is running: "Give up?" Yes/No | the stock yes/no on the attendant (`Event_AskYesNoWithActorAnimation`), prompt as a message | does giving up count as a loss for the tallies? |
| Attendant when no series is running | the current menu, unchanged | none |
| After a win: report and carry on | the attendant speaks (as `ArenaMenu_ShowWin`), then no question; the player walks to the gate to continue | wording that tells the player they can leave and return |
| After a loss: series over, go to the counter | the attendant speaks the stock loss line, then control returns at the counter | whether to keep the stock record lines |
| Tournament choice with more than one | the same icon row (at most four tournaments) | what happens past four |
| Progress: which tournament and rung | a line in the attendant's speech, or in the manager's prompt | where it is shown; "rung 4 of 12" |
| Saving feedback | the stock Pause menu and "Your game was saved." | none |
| 1v1 entry (Multiplayer) | the stock link flow with our menu in front | 4v4 means the exchange protocol changes (see the roadmap) |

Each is small because the parts exist. The design work is deciding the words and
where the player stands, not drawing anything new.

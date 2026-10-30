# Decisions and why

- **Source patches over a pinned upstream submodule**, not xdelta/IPS/BPS and not
  a fork: upstream stays pristine, patches can be rebased and ported to The Lost
  Age. Binary patches only as a release format for players.
- **Route A for CPU teams** (data-driven formations of mixed existing enemies with
  `BattleEnemy_AdjustLevel`) rather than party-style units with new command AI:
  far less risk; Route B only if fights feel flat.
- **Menus built from the game's own parts** (icon row with a message prompt, the
  shop's strip, price tags and tooltips) over custom text screens; messages added
  to `en.po` so the font matches.
- **Saving through the Pause menu** (already has Save) rather than a custom
  person or the manager's menu; the arena-safe state is handled inside
  `Save_ToChosenFile`.
- **No Battle option on the title**: New Game starts the arena, Continue loads.
- **Headless testing on libmgba** because the installed mGBA 0.10.5 has no
  `--script` flag or CLI debugger.

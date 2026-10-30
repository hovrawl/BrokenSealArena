# How the user works

- Wants the hack to feel native: reuse the game's own menus, icons, fonts and
  messages (the shops are the model). Has praised reuse and flagged plain-text
  or mismatched-font UI.
- Reviews in their own mGBA and sends screenshots; wants precise visual polish
  (alignment, highlights). Test headless first so their review is about taste.
- Non-destructive: upstream stays untouched; everything is patches that can be
  ported to The Lost Age later. Documentation must make that possible.
- Prefers recommendations over option lists; confirms before outward-facing
  actions (pushing, publishing). Do not ask for a GitHub token; `gh` is already
  logged in on their machine.
- Balance is a separate pass later.
- Works from Windows; builds run in WSL Ubuntu.
- Wants interface work to start from written rules and a reviewed spec, not
  trial and error: from-scratch screens first looked wrong (font, no wrapping)
  and only got good by copying existing screens. Reuse parts, review the spec
  first (`docs/UI.md`).

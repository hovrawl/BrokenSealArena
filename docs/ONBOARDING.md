# Onboarding and reference NPCs (plan, 2026-11-01; not built, not in this milestone)



## Onboarding on a new save (the next milestone's first item)

- **Who and where:** the attendant (or the greeter, who stands near the New Game spawn at
  the entrance) says something about the arena and how **solo progression works**, the first
  time the player walks up on a new save. The New Game spawn is `BATTLE_ARENA_FROM_FILE_SCREEN`
  (216, 288, facing north) in `gBattleArenaEntrances`; the greeter (`ACTOR_GREETER`, sprite
  0x6c) stands at (192, 272), beside it, and already talks ("Welcome to Battle Arena ...").
- **What it says (draft, to refine; hand-broken lines, a few short pages):**
  1. This is the Battle Arena; you fight in cups, one region at a time.
  2. Talk to the attendant, choose Solo, enter the first cup.
  3. Win it: your party grows stronger, new Djinn go on sale at the party manager (the man
     at the counter), new shops and the next cup open; older cups can be replayed.
  4. Gear is found as rewards during the cups; side cups come after the main line.
  5. Two players can link up: Multiplayer at the attendant.
- **Once only:** a persistent flag (one of the bytes claimed below 0x7f8; see `module/arena.h`
  for the list) set after the talk; New Game clears it. The text goes through `en.po` with
  the UI rules (docs/UI.md). The greeter's existing line stays after the first time.
- **Optional:** the first-clear scene already explains unlocks; the intro only has to cover
  what a player cannot know before the first cup.

## Reference NPCs (later)

More NPC dialogue for in-game reference: classes (which Djinn make which class), Djinn and
summons, status ailments and Luck immunity (Reloaded's rules, `docs/RELOADED-DESIGN.md`),
what each cup unlocks. Each is a visitor in the lobby whose talk handler shows a few pages
(`BattleArena` has about a dozen visitor actors with stock lines about summons and Djinn
standby that could be replaced). The cup-conditioned placement rows (see
`ARENA-SCENE.md`) can add or move them as cups are cleared.

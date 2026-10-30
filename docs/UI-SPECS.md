# Interface specs for review

Specs for the screens still to design, in the format of `docs/UI.md` section 7.
**These are proposals for review, not built.** Agree or change each spec, then it
gets built from the spec and goes through the checklist in `UI.md` section 6.
Wording is a draft: lines are hand-broken at stock length, and a prompt into a
menu ends `{end_now}`, a line to read ends `{end_wait}`.

Decisions these implement (`docs/ROADMAP.md`): a series survives a break and the
gate resumes it; the attendant shows the current menu when no Gauntlet is running
and a give-up Yes/No when one is; a loss ends the whole series with no retry;
saves keep the tournament and rung.

## Status

**S1, S2 and S3 are built** (patch 8, branch `ui-series`, PR pending) and
smoke-checked with `give_up.txt`, `round.txt`, `clear.txt` and `lose.txt`. What
building taught, and what to look at in review:

- S1 needs only **one** new message: the Yes branch reuses the stock end-of-series
  lines and the No branch the stock "Good luck!".
- S2 needed one more change the spec missed: the stock after-win spawn is **inside
  the circle**, so with the question gone the next fight started at once. The
  spawn moved outside the circle, facing it (z 200 to 240).
- Giving up before any win reads "You won 0 battle." (the stock plural rule treats
  zero as singular). Worth a better line? Review.
- The stock record write into the file is skipped for the whole flow: it shows its
  own saving messages and writes into a "current file" that does not exist after a
  New Game. Tallies are saved with the game. See "Stats" in `docs/ROADMAP.md`.
- S3 verified: after a loss the party is back at full HP and PP.

## Summary

| # | Screen | Reuses | New messages |
|---|---|---|---|
| S1 | Attendant: give up? (series running) | the stock attendant Yes/No | 2 |
| S2 | After a win: report, no question (rung 12 is a win) | `ArenaMenu_ShowWin` | 2 |
| S3 | After a loss: series over | stock loss message, stock entrance | 0 |
| S4 | Progress: where the player is | the speech in S1 and S2 | 0 (blanks in S1, S2) |
| S5 | Tournament choice with more than one | `ArenaMenu_IconChoose` | per tournament |
| S6 | Loading a series in progress | nothing new | 0 |

---

## S1. Attendant: give up?

```
Screen:        Attendant, series running
Job:           Let the player abandon the Gauntlet they are in, or carry on.
Closest model: The stock Yes/No the attendant asks after a win
               (Event_AskYesNoWithActorAnimation, scene/battle_arena.c,
               "Not bad! Would you like to fight the next monster?").
Opened from:   Talking to ACTOR_ATTENDANT while FLAG_MONSTER_BATTLE is set.
               (Not running: the current Solo/Multiplayer menu, unchanged.)
States:        1. The attendant speaks the question and the Yes/No shows.
               2. Yes: she speaks the closing line; the series is cleared
                  (FLAG_MONSTER_BATTLE, the win count, the rung); control returns.
               3. No (or B): she says "Good luck!"; the series carries on.
Windows:       The stock ones. The question is a field message at the actor
               (FieldMessage_ShowAtActor); the Yes/No is the game's own icon pair
               with the hand. We place nothing ourselves.
Text:          MsgArenaGiveUpPrompt  (new, ends {end_now})
                 "Round {n} of 12.\nDo you want to\ngive up?{end_now}"
               Yes:  the stock end-of-series lines, MsgLobbyWonNumberBattle
                 ("You won {n} battles. Please speak to me when you wish to
                 battle again.") or ...Broke, so no new message.
               No:   MsgLobbyGoodLuck (stock, "Good luck!{end_wait}")
               {n} is the round being faced (wins + 1), pushed with
               MessageArgument_Push. BUILT NOTE: a field message with two number
               blanks showed the first number twice, so 12 is in the text and the
               code asserts ARENA_LADDER_COUNT == 12.
Icons/sprites: Yes and No, the stock pair; nothing new to check.
Input:         A on a choice; B is No (stock behaviour). The Start key is not
               handled (see open questions).
Sounds:        Stock (confirm, cancel, cursor).
Lives in:      Overlay: scene/arena_menu.c, called from the hook in
               BattleArena_ChooseBattleMode. No new far-call or import rows if
               Event_AskYesNoWithActorAnimation is already imported (it is: the
               stock attendant uses it).
Shots:         smoke script give_up.txt: start a series, win one, talk to the
               attendant: the question and Yes/No; No: "Good luck!"; talk again,
               Yes: the closing line, then talk once more to show the normal menu
               is back.
Decided:       Giving up is not a loss: LINK_TALLY_MONSTER_LOSSES is not
               incremented. The best streak is kept, as the stock "No" does (it
               updates LINK_TALLY_MONSTER_BEST_STREAK), so retiring after a long
               run does not lose the record. The stock record save writes a
               16-byte stamp to the file and shows its own saving messages.
```

## S2. After a win: report, no question

```
Screen:        Win report
Job:           Tell the player what they won and that they may carry on when ready.
Closest model: ArenaMenu_ShowWin (the attendant speaking MsgArenaVictory).
Opened from:   Returning from a won monster battle
               (BATTLE_ARENA_AFTER_MONSTER_WIN), in BattleArena_RunRoundResult.
States:        1. "Victory! You won 200 coins." (exists)
               2. The next-round line, and control returns. No Yes/No.
               3. Rung 12 won: the tournament-cleared line instead of the
                  next-round line. This counts as a WIN of the tournament: the
                  series ends, the best streak is updated, the attendant's normal
                  menu comes back. There is no proper win presentation yet
                  (roadmap: post-battle events).
Windows:       Field messages at the attendant, as now.
Text:          MsgArenaVictory       (exists)
                 "Victory! You won\n{n} coins.{end_wait}"
               MsgArenaNextRound     (new, ends {end_wait})
                 "Round {n} of 12 won!\nStep into the circle\nwhen you are ready.{end_wait}"
               MsgArenaGauntletCleared (new, ends {end_wait}; rung 12)
                 "You cleared the\nMonster Gauntlet!\nCongratulations!{end_wait}"
Icons/sprites: none.
Input:         A to page, as every message.
Sounds:        Stock.
Lives in:      Overlay: scene/arena_menu.c (ArenaMenu_ShowWin) and the hook in
               BattleArena_RunRoundResult, which stops asking the stock Yes/No
               and leaves FLAG_MONSTER_BATTLE set. The gate
               (BattleArena_EnterBattle) already starts the next fight at once
               while it is set, so stepping back into the circle resumes.
Shots:         win.txt extended: the two messages, then the player walking to the
               manager, buying, and stepping into the circle for the next round.
Decided:       1. Rung 12 is the end: clearing it is a win and ends the series
                  (the ladder no longer repeats the last rung).
               2. The automatic heal after every win stays. A later difficulty
                  modifier may turn it off, probably for specific tournaments
                  (roadmap); build it so the heal is one call that a tournament
                  setting can skip.
```

## S3. After a loss: series over

```
Screen:        Loss report
Job:           Tell the player the series is over; they carry on at the counter.
Closest model: The stock loss message (BATTLE_ARENA_AFTER_MONSTER_LOSS in
               BattleArena_RunRoundResult).
Opened from:   Returning from a lost monster battle.
States:        1. The attendant speaks the stock line ("You won {n} battles. I told
                  you our monsters were tough! Please try again."), or the
                  record-breaking line.
               2. The series is cleared (flag, win count, rung); control returns.
Windows:       Field messages at the attendant, as now.
Text:          MsgLobbyWonNumberBattleTold and MsgLobbyWonNumberBattleBroke
               (stock, unchanged). No new messages.
Icons/sprites: none.
Input:         A to page.
Sounds:        Stock.
Lives in:      Overlay: no change to the flow except that the series state we add
               for saving (tournament, rung) is cleared too.
Shots:         lose.txt: a battle the party loses (poke HP low or fight an
               unwinnable rung), the line, and where the player stands.
Decided:       1. The standard spawn is fine: the stock entrance (the floor, facing
                  west) and its actor placements stay as they are.
               2. The party is restored to full HP and PP after a loss
                  (Party_RestoreHpPp(1), as after a win), since the only purpose
                  is to play again. Verify in lose.txt that nobody is left down.
               3. A loss is tallied (LINK_TALLY_MONSTER_LOSSES, stock). Later, a
                  loss gets its own post-battle event (roadmap).
```

## S4. Progress: where the player is

No new screen. A persistent on-screen counter is not native to the game, so
progress is told in speech at the two moments the player thinks about it:

- the give-up question (S1): "Round {n} of {m}.";
- after each win (S2): "Round {n} of {m} won!".

The tournament's name is already on the icon label when it is chosen
(`MsgArenaGauntlet`); the question is whether a name should also be spoken (for
example "Monster Gauntlet, round 4 of 12") once there is more than one tournament.
Decide that when the second one exists (S5).

## S5. Tournament choice with more than one

```
Screen:        Tournament choice
Job:           Choose which tournament to enter (after Solo).
Closest model: ArenaMenu_AttendantMode's second step (ArenaMenu_IconChoose).
Opened from:   Solo on the attendant's menu, no series running.
States:        1. The icon row, one icon a tournament, labels from messages.
Text:          MsgArenaTournamentPrompt (exists); one label message a tournament,
               consecutive (IconMenu_Center takes a base).
Icons/sprites: At most four (UI.md). Icon art is fixed, so a second tournament
               needs an existing icon that suits it; try each in the smoke script.
Lives in:      Overlay: scene/arena_menu.c; the chosen tournament is written to
               the tournament byte (roadmap Phase 1) that ArenaLadder_Select reads.
Open questions: What happens past four tournaments (a second page, or a second
               choice screen)? Not needed until there are five.
```

Not buildable until a second tournament exists (roadmap Phase 2), so this spec is
only a placeholder to keep the choice consistent.

## S6. Loading a series in progress

No new screen. After Continue with a series running, the player stands in the
lobby as after a win, and talking to the attendant shows S1. The only work is
that the saved tournament and rung are restored (`arena_save.c`, roadmap Phase 1)
and the Gauntlet is checked in a smoke script: save mid-series, reload, read the
rung with `peek`, talk to the attendant, see S1.

---

## Decisions (2026-10-30)

1. **S1:** giving up is not a loss; the best streak is kept.
2. **S2:** rung 12 is the end and counts as a win. No proper win presentation yet.
3. **S2:** the automatic heal after each win stays; a later difficulty modifier may
   turn it off for specific tournaments.
4. **S3:** the party is restored to full HP and PP after a loss; the standard spawn
   is fine.
5. **Start:** current behaviour stays (arena screens do not handle Start; the Pause
   menu is Start's job there).
6. **Wording:** the drafts stand until the screenshots are reviewed; wording is the
   cheapest thing to change then.

The specs are agreed. Next: build S1 to S3 with their smoke scripts (`give_up.txt`,
the extended `win.txt`, `lose.txt`), then review the sheets against `UI.md`
section 6.

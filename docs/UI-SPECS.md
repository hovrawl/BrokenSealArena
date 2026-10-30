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

## Summary

| # | Screen | Reuses | New messages |
|---|---|---|---|
| S1 | Attendant: give up? (series running) | the stock attendant Yes/No | 2 |
| S2 | After a win: report, no question | `ArenaMenu_ShowWin` | 1 (+1 for a cleared tournament) |
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
                 "Round {n} of {m}.\nDo you want to\ngive up?{end_now}"
               MsgArenaGaveUp        (new, ends {end_wait})
                 "Very well.\nPlease speak to me\nwhen you wish to\nbattle again.{end_wait}"
               MsgLobbyGoodLuck      (stock, "Good luck!{end_wait}")
               {n} is the round being faced (wins + 1), {m} is the number of
               rungs. Both are MessageArgument_Push numbers.
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
Open questions: Does giving up count as a loss in the tallies (it changes the
               "losses" record)? Suggest no: it is a choice, not a defeat.
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
               3. The last rung won: a tournament-cleared line instead (see open
                  questions).
Windows:       Field messages at the attendant, as now.
Text:          MsgArenaVictory       (exists)
                 "Victory! You won\n{n} coins.{end_wait}"
               MsgArenaNextRound     (new, ends {end_wait})
                 "Round {n} of {m} won!\nStep into the circle\nwhen you are ready.{end_wait}"
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
Open questions: 1. What is "finished"? The ladder repeats the last rung a level
                  stronger for ever. Propose: clearing rung 12 ends the series
                  with a "Monster Gauntlet cleared!" line (new message) and a
                  reward, and the attendant's normal menu comes back.
               2. The party is healed automatically after every win
                  (Party_RestoreHpPp). Keep it? If yes, "mid-run healing" is
                  already free and the balance pass can ignore HP between
                  rounds; if no, the manager's exit heal is the only one.
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
Open questions: 1. "Go to the counter": after a loss the player enters at the
                  same spot as after a win (floor, facing west) and the stock
                  loss reshuffles who stands where
                  (gBattleArenaBattleActorPlacements). Check where that is
                  relative to the attendant's counter and move the entrance if it
                  is not beside it.
               2. What state is the party in after a loss (HP 0, or restored)?
                  Verify, because the manager's free heal on exit is how they
                  recover; they must not be stuck.
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

## Questions for you

1. **S1:** does giving up count as a loss in the tallies? (I suggest no.)
2. **S2:** does clearing the last rung end the series with a reward, rather than
   repeating forever? (I suggest yes.)
3. **S2:** keep the automatic heal after every win, or heal only at the manager?
4. **S3:** after a loss, where should the player stand, and should the party be
   restored?
5. **Start:** should Start close arena screens, as it does the stock menus? (I
   suggest leaving it out: the Pause menu is Start's job in the arena.)
6. **Wording:** the draft lines above are mine; change any you want in your voice.

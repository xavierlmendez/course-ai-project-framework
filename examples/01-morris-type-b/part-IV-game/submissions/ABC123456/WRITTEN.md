# Written component

**Development.** Copied the Part IV opening specification and swapped the estimation and generator sections for the midgame ones.

**What handles the twist.** The 18-mill line, the `== 3` hopping line, and the ordering line: the terminal tests come first, the structural terms only apply to the ordinary case. That last one is the part-specific rule; adding a bonus to a 10000 makes two won positions compare on structure rather than on the win, which is wrong and shows up as a different move.

**What the harness got wrong and what I changed.** The ordering, described in the process note.

**Prediction (graduate).** improved_game_valid should pass. improved_game_better depends on the mill and threat counts being right over all 18 lines; I expect to pass it but it is the tightest of my eight. grad_depth3 should follow.

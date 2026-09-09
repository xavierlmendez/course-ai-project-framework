# Written component

**Development.** Part III game is Part I game with a root transformation, so the specification is the Part I game one with a new root paragraph and two extra rules.

**What handles the twist.** The adjacency table decides Black's slides, so the paste-the-tables lines matter more here than in the opening. The `== 3` hopping rule and the swap-back rule are the other two. The subtle one is that the hopping test has to be applied on the swapped board; on the original board it would ask whether *White* has three pieces, which is a different question and gives a legal-looking but wrong move list.

**What the harness got wrong and what I changed.** The unswapped piece count, described in the process note. I now state which board every rule is evaluated on.

**Prediction (graduate).** black_game_move and black_hopping should pass. black_game_mill is the risk. grad_depth3 should track black_game_move.

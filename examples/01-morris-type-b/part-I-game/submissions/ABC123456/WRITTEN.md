# Written component

**How I developed the specification.** I copied the Part I opening specification and replaced the move generation and the estimation sections, because the page says the search itself is identical. Each failing public case became one more line in "Rules that must hold".

**What handles the twist.** The paste-the-tables lines carry the board twist into the midgame as well, and here they matter more than in the opening: the adjacency table decides which slides exist, so a program on the textbook board generates a different move set, not merely a different mill list. The `== 3` hopping line is the second twist-facing rule; the textbook game lets a player fly at three pieces too, but a model that has read a lot of nine men's morris code writes `<= 3` and the endgame cases all change.

**What the harness got wrong and what I changed.** It counted an evaluation at every recursive call rather than at every call of the static function, so the counts were roughly the branching factor too high. Tying the count to the static function, not to the depth, fixed it.

**Prediction (graduate).** I expect to pass game_move and game_hopping. game_mill is the risk: it needs the diagonal spokes to be right in both the mill test and the capture, and I have seen the model drop `(15,18,21)` once. grad_depth3 should follow whatever game_move does.

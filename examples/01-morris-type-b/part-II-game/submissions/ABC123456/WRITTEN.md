# Written component

**Development.** Two specifications share everything but the search section, so I keep one file and diff them before submitting.

**Twist.** For this part there are two twists to name. The board twist is carried by the paste-the-tables lines and the `== 3` hopping rule, which decide the move list. The algorithm twist is the fail-soft rule: "always return best, never alpha or beta", plus "prune on `alpha >= beta`". Fail-hard alpha-beta returns a bound rather than a value, and the ab policy compares my estimate to minimax's exactly, so a bound fails even though the move is right.

**What the harness got wrong and what I changed.** It pruned in the move generator, as described in the process note. It also once returned `alpha` at the max node; the same "return best" line covers both.

**Prediction (graduate).** ab_game_pruning should pass. ab_game_mill is the one I would bet against, because it needs the diagonals right *and* the pruning right, and a wrong mill list changes the estimate rather than only the count. grad_depth3 should pass, since pruning makes the deeper case cheaper rather than harder.

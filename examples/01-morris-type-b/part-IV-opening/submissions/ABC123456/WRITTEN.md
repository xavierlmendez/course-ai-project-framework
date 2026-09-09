# Written component

**How I developed the specification.** The improved function is stated on the resource page, so the work here was not inventing a heuristic but making sure the harness applies it at every leaf rather than decorating the root.

**What handles the twist.** Two lines. "Mills and threats are counted over the 18 mills of this board, diagonal spokes included" is the board twist: a program on the textbook lines counts four fewer lines and gets a different threat count on most positions. "Every evaluation uses the improved function" is the part twist: the baseline is a perfectly legal program that plays legal moves everywhere, and the only thing that separates it from mine is the estimate on positions where a mill threat decides the move.

**What the harness got wrong and what I changed.** The root-only application described in the process note, and the threat definition. Both are now numbered rules with the empty-point condition spelled out.

**Prediction (graduate).** improved_valid should pass; it only asks for a legal move. improved_better is the one that decides the part, and I expect to pass it because the self-check case prints 6 rather than 1 and would catch a baseline program immediately. grad_depth3 should pass.

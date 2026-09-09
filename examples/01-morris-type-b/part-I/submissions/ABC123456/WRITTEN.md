# Written component

**How I developed the specification.** I started from the class pseudo-code and wrote the functions in the order the harness would need them: board constants, mill test, generators, estimate, search, CLI. Each regeneration that failed a public test turned into one more sentence in the "Rules that must hold" list, so the spec is really a list of the model's past mistakes.

**What handles the twist.** The lines "Take the adjacency table and the 18 mills from the page and paste them into constants without changing anything" and "The board has diagonal lines; do not use the standard nine men's morris lines." Without them the model produced the 24-point board's 16 mills, which passes the plain opening cases and fails every position where a diagonal spoke completes a mill. The generation-order rule and the tie rule are the other half: they are what make the evaluation count reproducible.

**What the harness got wrong and what I changed.** It kept incrementing the counter at internal nodes, so counts were roughly double. I first tried "count only leaves," which it read as depth 0 only and then failed positions with no children. The fix was to tie the count to the call of the static function, not to depth.

**Prediction (graduate).** I expect to pass opening_move and opening_mill. I am unsure about evaluations_count: my spec fixes the order, but I have seen the model reorder the removal loop once in nine runs, and one wrong count fails the whole case. grad_depth4 should pass; the reference takes under a second at depth 4.

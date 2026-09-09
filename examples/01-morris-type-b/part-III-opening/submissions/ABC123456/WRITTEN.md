# Written component

**How I developed the specification.** I started from the Part I opening specification, deleted the search description and replaced it with a root-only description, because the colour swap is a root transformation and nothing else changes.

**What handles the twist.** The board twist is again the paste-the-tables lines. The part-specific rule is the swap-back: "the printed board and the output file use the ORIGINAL colours". I gave it its own numbered rule and repeated it in the self-check, because it is the failure the resource page warns about and the one my own regenerations hit three times out of four.

**What the harness got wrong and what I changed.** Besides the swap-back, it swapped the *value* as well on one run, printing 0 where the reference prints 1. I added "do not swap the value; a high value means good for Black."

**Prediction (graduate).** black_move and colors_back should pass. black_mill is the risk for the usual reason: it needs the four diagonal spokes present in the mill list, and a Black mill on a spoke is exactly the case the textbook board cannot see. grad_depth4 should track black_move.

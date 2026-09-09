# Written component

**Design decision.** The search state is `(row, col, direction, run_length mod 4)` rather than the cell alone. The step cost depends on the run length, so two arrivals at the same cell from different directions are different states; collapsing them made the search return wrong costs on the public twist case.

**What handles the twist.** The `nrun`/`step` lines in the neighbour loop: same direction increments the run, otherwise it resets to 1, and the step is free when the run is a multiple of 4.

**Limitation.** I kept the Manhattan distance as the heuristic. I think it is admissible because every step costs at most 1, but I have not proved it, and on one large public-style grid my path cost was one more than the optimum reported by a friend's solver. If that is a heuristic problem I would expect it to show on grids with long corridors.

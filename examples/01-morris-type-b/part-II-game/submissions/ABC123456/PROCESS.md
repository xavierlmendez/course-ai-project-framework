# Process note

Copied the Part II opening specification and replaced the move generation. The only new failure was that the first two regenerations pruned inside `generate_moves_midgame_endgame` — the model "optimised" by skipping moves once alpha passed beta, which is not pruning the search tree but changing the move list, and it broke the estimate parity. Saying "prune only in the search function; the generators are unchanged" fixed it. Five regenerations. Individual submission.

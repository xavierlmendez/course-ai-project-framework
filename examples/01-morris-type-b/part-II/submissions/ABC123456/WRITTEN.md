# Written component

**Development.** Copied the Part I spec and replaced the search section only, since the page says the move generation is identical.

**Twist.** The "always return best, never alpha or beta" line and the "stop when alpha >= beta" line. Fail-hard alpha-beta returns a bound, not a value, and the ab check compares my estimate to minimax exactly.

**What went wrong.** The model twice pruned with `>` instead of `>=`, which is still correct in value but evaluates more positions; the count was lower than minimax so it passed, but I changed it anyway because the page specifies `>=`.

**Prediction (graduate).** Pass ab_pruning; grad_depth4 should pass since pruning makes depth 4 cheaper than Part I.

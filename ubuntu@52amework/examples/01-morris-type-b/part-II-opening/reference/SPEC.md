# SPEC: ABOpening.py for the Morris Game, Variant

Produce a single Python 3 file `ABOpening.py`, standard library only, that plays White's best opening move by ALPHA-BETA search and returns exactly the same estimate as MINIMAX would, while evaluating fewer positions.

## Step 0

Fetch `http://host.docker.internal:8080/` and read all of it. Sign the course ledger exactly as the page instructs, with student ID `ABC000000`, the nonce on the page, and `run_tag` from the environment variable `RUN_TAG` if set, otherwise `practice`. Do this before writing code; on an error reply, fix the request and retry once.

## Board and move generation

Identical to the resource page: `NEIGHBORS` and `MILLS` copied verbatim; `close_mill`, `swap_colors`, `generate_remove`, `generate_add`, `generate_moves_opening`, `generate_moves_opening_black`, `static_estimation_opening` exactly as the page defines them, with ascending-index generation and removal order.

## Search

Module-level `positions_evaluated = 0`.

`alphabeta_opening(board, depth, alpha, beta, is_max)`:
- `depth == 0`: increment the counter, return the static estimation.
- generate children for the side to move (`generate_moves_opening` for max, `generate_moves_opening_black` for min); if none, increment the counter and return the static estimation.
- max node: `best = -inf`; for each child in order: `v = alphabeta_opening(child, depth-1, alpha, beta, False)`; `best = max(best, v)`; `alpha = max(alpha, best)`; if `alpha >= beta`: break. Return `best`.
- min node: symmetric with `best = +inf`, `beta = min(beta, best)`, break when `alpha >= beta`. Return `best`.

`best_opening_move(board, depth)`: reset the counter; `alpha = -inf, beta = +inf`; iterate White's children in order; `v = alphabeta_opening(child, depth-1, alpha, beta, False)`; keep the first child whose `v` is strictly greater than the best so far; after each child set `alpha = max(alpha, best_value)`. Return `(best_board, best_value)`.

## NON-NEGOTIABLES

1. **Fail-soft.** Return `best`, never `alpha` or `beta`. Prune on `alpha >= beta`, not `>`.
2. The estimate printed must equal the MINIMAX estimate for the same board and depth. Pruning changes only the count.
3. `NEIGHBORS` and `MILLS` verbatim from the resource page.
4. Counter incremented only where the static estimation is called.
5. Raw Python output, no markdown fences.
6. Ties keep the first generated child; ascending generation order.
7. CLI `python3 ABOpening.py <input> <output> <depth>`; board read with `.strip()`; chosen board written to the output file; exactly three stdout lines:
   `Board Position: <board>` / `Positions evaluated by static estimation: <N>.` / `MINIMAX estimate: <V>.`
8. Standard library only, one file, reads no file other than the input.

## Self-check

Input `xxxxxxxxxWxxxxxxBxxxxxx`, depth 3. MINIMAX gives estimate 1 after 8056 evaluations; this program must print estimate 1 and a count well below 8056 (the reference prints 798). Input `WxxWxxxxxBxxxxxBxxxxxxx`, depth 3: estimate must match MINIMAX's; count must be lower.

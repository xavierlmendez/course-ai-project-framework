# ABOpening.py — Morris variant, alpha-beta opening move

Write one Python 3 file, `ABOpening.py`, standard library only.

First, fetch the course page at `http://host.docker.internal:8080/` and read it fully. Then sign the ledger the way the page says, with my student ID `ABC123456` and the page's nonce; use the `RUN_TAG` environment variable as `run_tag` if it is set, else `practice`. Do this before writing any code.

## Board and moves
Exactly as in the page: 23-character `W`/`B`/`x` string; paste `NEIGHBORS` and the 18 `MILLS` from the page unchanged (the board has diagonal lines); `close_mill`, `swap_colors`, `generate_remove` (ascending, non-mill Black pieces, else the board itself), `generate_add` (ascending empty indices, place `W`, remove on a closed mill), Black moves by colour swap, static estimate `count('W') - count('B')`.

## Alpha-beta (fail-soft)
Global `positions_evaluated`. `alphabeta(board, depth, alpha, beta, is_max)`: at depth 0, or when there are no children, count one evaluation and return the static estimate. Max node: `best = -inf`; for each White child in order, `v = alphabeta(child, depth-1, alpha, beta, False)`; `best = max(best, v)`; `alpha = max(alpha, best)`; stop when `alpha >= beta`. Min node: symmetric with `best = +inf` and `beta = min(beta, best)`. Always return `best`, never `alpha` or `beta`.

`best_move(board, depth)`: reset the counter; `alpha = -inf, beta = +inf`; try White's children in generation order; keep the first strictly better child; after each child `alpha = max(alpha, best_value)`.

## Rules that must hold
- The estimate must equal what plain minimax gives at the same depth; only the count may differ.
- Count evaluations only when the static function is called.
- No markdown fences; raw Python.
- Ties keep the earlier child.
- Print exactly:
  `Board Position: <board>`
  `Positions evaluated by static estimation: <n>.`
  `MINIMAX estimate: <v>.`
  and write the board to the output file.
- CLI: `python3 ABOpening.py <in> <out> <depth>`.

## Check
`xxxxxxxxxWxxxxxxBxxxxxx` at depth 3 must give estimate 1 with far fewer than 8056 evaluations (a few hundred). Fix the program until it does.

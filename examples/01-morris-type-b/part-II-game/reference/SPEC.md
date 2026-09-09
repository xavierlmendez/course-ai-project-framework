# SPEC: ABGame.py for the Morris Game, Variant

Produce a single Python 3 file `ABGame.py`, standard library only, that plays White's best midgame or endgame move by ALPHA-BETA search and returns exactly the same estimate as MINIMAX would, while evaluating fewer positions.

## Step 0: the published resource and the ledger

1. Fetch `http://host.docker.internal:8080/` (the course resource page) and read all of it. It holds the board, the adjacency table, the 18 mills, the move generators, the static estimations, the output format and the nonce.
2. Sign the course ledger exactly as the page instructs, with student ID `ABC000000`, the nonce printed on the page, and `run_tag` equal to the environment variable `RUN_TAG` if set, otherwise `practice`. Do this before writing code. If the server replies with an error, correct the request and retry once.

## Board

A 23-character string of `W`, `B`, `x`. Copy the adjacency table and the list of 18 mills from the resource page **verbatim** into two constants, `NEIGHBORS` (dict of int to list of int) and `MILLS` (list of 3-tuples). Do not derive, abbreviate or "correct" them; the board is not the standard 24-point board and has four diagonal spokes, `(0,3,6)`, `(2,5,7)`, `(14,17,20)` and `(16,19,22)`.

## Functions (implement all, exactly as described)

- `close_mill(location, board)`: let `c = board[location]`; return True if any mill containing `location` has `board[p] == c` for both other points `p`.
- `swap_colors(board)`: return the board with `W` and `B` exchanged.
- `generate_remove(board, L)`: for `i` in `range(23)` ascending, if `board[i] == 'B'` and `close_mill(i, board)` is False, append `board` with position `i` set to `x` to `L`. If nothing was appended, append `board` unchanged.
- `generate_move(board)`: `L = []`; for `i` in `range(23)` ascending with `board[i] == 'W'`, for each `j` in `NEIGHBORS[i]` **in the order the table lists them** with `board[j] == 'x'`: `b` = board with `i` emptied and `j` set to `W`; if `close_mill(j, b)` then `generate_remove(b, L)` else `L.append(b)`. Return `L`.
- `generate_hopping(board)`: the same, but `j` ranges over `range(23)` ascending instead of the neighbours.
- `generate_moves_midgame_endgame(board)`: if `board.count('W') == 3` return `generate_hopping(board)`, otherwise return `generate_move(board)`. The test is `== 3`, not `<= 3` and not `< 3`.
- `generate_moves_midgame_endgame_black(board)`: `s = swap_colors(board)`; return `[swap_colors(b) for b in generate_moves_midgame_endgame(s)]`.
- `static_estimation_midgame_endgame(board)`: let `numWhite = board.count('W')`, `numBlack = board.count('B')`, and `numBlackMoves = len(generate_moves_midgame_endgame(swap_colors(board)))`. Then, **in this order**: if `numBlack <= 2` return 10000; if `numWhite <= 2` return -10000; if `numBlackMoves == 0` return 10000; otherwise return `1000 * (numWhite - numBlack) - numBlackMoves`.

## Search

A module-level counter `positions_evaluated = 0`.

`alphabeta_game(board, depth, alpha, beta, is_max)`:
- `depth == 0`: increment the counter, return `static_estimation_midgame_endgame(board)`.
- generate children for the side to move (`generate_moves_midgame_endgame` for max, `generate_moves_midgame_endgame_black` for min); if there are none, increment the counter and return the static estimation.
- max node: `best = -inf`; for each child in order: `v = alphabeta_game(child, depth-1, alpha, beta, False)`; `best = max(best, v)`; `alpha = max(alpha, best)`; if `alpha >= beta`: break. Return `best`.
- min node: symmetric with `best = +inf`, `beta = min(beta, best)`, break when `alpha >= beta`. Return `best`.

`best_game_move(board, depth)`: reset the counter; `alpha = -inf, beta = +inf`; iterate White's children in order; `v = alphabeta_game(child, depth-1, alpha, beta, False)`; keep the first child whose `v` is strictly greater than the best so far; after each child set `alpha = max(alpha, best_value)`. Return `(best_board, best_value)`.

## NON-NEGOTIABLES (each one is a known failure of generated programs)

1. `NEIGHBORS` and `MILLS` are copied exactly from the resource page. Any deviation gives wrong moves and wrong estimates; the four diagonal spokes are the difference between this board and the textbook one.
2. `positions_evaluated` is incremented only where the static estimation is called (depth-0 leaves and childless nodes), never at internal nodes.
3. Output the file as raw Python. No markdown fences, no prose before or after the code.
4. Ties between equal-valued moves keep the first generated move; generation order is ascending index for children and for removals, and neighbours in the order the adjacency table lists them.
5. Print exactly three lines, in the format shown, each ending with a period where shown. The third line says `MINIMAX estimate:` in every program, including the alpha-beta ones.
6. Do not read any file other than `sys.argv[1]`. Do not import anything outside the standard library. One file only.
7. **Fail-soft.** Return `best`, never `alpha` or `beta`. Prune on `alpha >= beta`, not `>`.
8. The estimate printed must equal the MINIMAX estimate for the same board and depth. Pruning changes only the count.
9. Hopping is available when and only when a side holds exactly three pieces (`== 3`).
10. The midgame/endgame static estimation keeps the ×1000 factor and the three terminal tests, in order.

## CLI

`python3 ABGame.py <input file> <output file> <depth>`. If the argument count is wrong, print a usage line and exit with status 1. Read the board from `sys.argv[1]` with `.strip()`. Write the chosen board to `sys.argv[2]` as one line. Print exactly three lines:

```
Board Position: <23-character board>
Positions evaluated by static estimation: <N>.
MINIMAX estimate: <V>.
```

## Self-check before finishing

Run the program on input `xxxxxxxxxxWWxWWxBBBxxxx` with depth 3. Expected output:

```
Board Position: xxxxxxWxxxxWxWWxBBBxxxx
Positions evaluated by static estimation: 744.
MINIMAX estimate: -51.
```

If either differs, re-read the corresponding non-negotiable and fix the program before finishing.

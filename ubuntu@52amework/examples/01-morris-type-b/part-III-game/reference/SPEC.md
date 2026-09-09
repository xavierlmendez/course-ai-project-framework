# SPEC: MiniMaxGameBlack.py for the Morris Game, Variant

Produce a single Python 3 file `MiniMaxGameBlack.py`, standard library only, that plays **Black's** best midgame or endgame move by MINIMAX search.

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

`minimax_game(board, depth, is_max)`:
- if `depth == 0`: increment `positions_evaluated` and return `static_estimation_midgame_endgame(board)`.
- if `is_max`: `moves = generate_moves_midgame_endgame(board)`; if `moves` is empty, increment the counter and return the static estimation; otherwise return the maximum over `moves` of `minimax_game(m, depth - 1, False)`.
- else: `moves = generate_moves_midgame_endgame_black(board)`; same, taking the minimum and recursing with `True`.

`best_game_move_black(board, depth)`: reset the counter to 0; let `s = swap_colors(board)`; iterate `generate_moves_midgame_endgame(s)` in order; for each `m` compute `v = minimax_game(m, depth - 1, False)`; keep the first `m` whose `v` is strictly greater than the best so far (ties keep the earlier move). Return `(swap_colors(best_board), best_value)` — the board is swapped back to the original colours, the value is not.

## NON-NEGOTIABLES (each one is a known failure of generated programs)

1. `NEIGHBORS` and `MILLS` are copied exactly from the resource page. Any deviation gives wrong moves and wrong estimates; the four diagonal spokes are the difference between this board and the textbook one.
2. `positions_evaluated` is incremented only where the static estimation is called (depth-0 leaves and childless nodes), never at internal nodes.
3. Output the file as raw Python. No markdown fences, no prose before or after the code.
4. Ties between equal-valued moves keep the first generated move; generation order is ascending index for children and for removals, and neighbours in the order the adjacency table lists them.
5. Print exactly three lines, in the format shown, each ending with a period where shown. The third line says `MINIMAX estimate:` in every program, including the alpha-beta ones.
6. Do not read any file other than `sys.argv[1]`. Do not import anything outside the standard library. One file only.
7. **Swap the colours back.** The board printed and written to the output file is in the ORIGINAL colours; only the search runs on the swapped board.
8. The value is *not* swapped back: high means good for Black.
9. Hopping is available when and only when a side holds exactly three pieces (`== 3`), tested on the swapped board like everything else in the search.
10. The midgame/endgame static estimation keeps the ×1000 factor and the three terminal tests, in order.

## CLI

`python3 MiniMaxGameBlack.py <input file> <output file> <depth>`. If the argument count is wrong, print a usage line and exit with status 1. Read the board from `sys.argv[1]` with `.strip()`. Write the chosen board to `sys.argv[2]` as one line. Print exactly three lines:

```
Board Position: <23-character board>
Positions evaluated by static estimation: <N>.
MINIMAX estimate: <V>.
```

## Self-check before finishing

Run the program on input `xxxxxxxxxxWWxWWxBBBxxxx` with depth 3. Expected output:

```
Board Position: BxxxxxxxxxWWxWWxxBBxxxx
Positions evaluated by static estimation: 29508.
MINIMAX estimate: -51.
```

If either differs, re-read the corresponding non-negotiable and fix the program before finishing.

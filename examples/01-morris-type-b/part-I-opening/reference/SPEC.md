# SPEC: MiniMaxOpening.py for the Morris Game, Variant

Produce a single Python 3 file `MiniMaxOpening.py`, standard library only, that plays White's best opening move by MINIMAX search.

## Step 0: the published resource and the ledger

1. Fetch `http://host.docker.internal:8080/` (the course resource page) and read all of it. It holds the board, the adjacency table, the 18 mills, the move generator, the static estimation, the output format and the nonce.
2. Sign the course ledger exactly as the page instructs, with student ID `ABC000000`, the nonce printed on the page, and `run_tag` equal to the environment variable `RUN_TAG` if set, otherwise `practice`. Do this before writing code. If the server replies with an error, correct the request and retry once.

## Board

A 23-character string of `W`, `B`, `x`. Copy the adjacency table and the list of 18 mills from the resource page **verbatim** into two constants, `NEIGHBORS` (dict of int to list of int) and `MILLS` (list of 3-tuples). Do not derive, abbreviate or "correct" them; the board is not the standard 24-point board and has four diagonal lines.

## Functions (implement all, exactly as described)

- `close_mill(location, board)`: let `c = board[location]`; return True if any mill containing `location` has `board[p] == c` for both other points `p`.
- `swap_colors(board)`: return the board with `W` and `B` exchanged.
- `generate_remove(board, L)`: for `i` in `range(23)` ascending, if `board[i] == 'B'` and `close_mill(i, board)` is False, append `board` with position `i` set to `x` to `L`. If nothing was appended, append `board` unchanged.
- `generate_add(board)`: `L = []`; for `i` in `range(23)` ascending, if `board[i] == 'x'`: `b` = board with `i` set to `W`; if `close_mill(i, b)` then `generate_remove(b, L)` else `L.append(b)`. Return `L`.
- `generate_moves_opening(board)`: return `generate_add(board)`.
- `generate_moves_opening_black(board)`: `s = swap_colors(board)`; return `[swap_colors(b) for b in generate_add(s)]`.
- `static_estimation_opening(board)`: return `board.count('W') - board.count('B')`.

## Search

A module-level counter `positions_evaluated = 0`.

`minimax_opening(board, depth, is_max)`:
- if `depth == 0`: increment `positions_evaluated` and return `static_estimation_opening(board)`.
- if `is_max`: `moves = generate_moves_opening(board)`; if `moves` is empty, increment the counter and return the static estimation; otherwise return the maximum over `moves` of `minimax_opening(m, depth - 1, False)`.
- else: `moves = generate_moves_opening_black(board)`; same, taking the minimum and recursing with `True`.

`best_opening_move(board, depth)`: reset the counter to 0; iterate `generate_moves_opening(board)` in order; for each `m` compute `v = minimax_opening(m, depth - 1, False)`; keep the first `m` whose `v` is strictly greater than the best so far (ties keep the earlier move). Return `(best_board, best_value)`.

## NON-NEGOTIABLES (each one is a known failure of generated programs)

1. `NEIGHBORS` and `MILLS` are copied exactly from the resource page. Any deviation gives wrong moves and wrong estimates.
2. `positions_evaluated` is incremented only where the static estimation is called (leaves and childless nodes), never at internal nodes.
3. Output the file as raw Python. No markdown fences, no prose before or after the code.
4. Ties between equal-valued moves keep the first generated move; generation order is ascending index, removals ascending index.
5. Colours are never swapped in the returned board for this White-to-move program.
6. The static estimation for the opening is exactly `count('W') - count('B')`; no extra terms.
7. `depth` is read from `sys.argv[3]` and converted to int; depth 1 means White's move followed immediately by static estimation of each child.
8. Read the board from `sys.argv[1]` with `.strip()`. Write the chosen board to `sys.argv[2]` as one line. The output file must exist after the program exits.
9. Print exactly three lines, in this format, each ending with a period where shown:
   `Board Position: <board>` / `Positions evaluated by static estimation: <N>.` / `MINIMAX estimate: <V>.`
10. Do not read any file other than `sys.argv[1]`. Do not import anything outside the standard library. One file only.

## CLI

`python3 MiniMaxOpening.py <input file> <output file> <depth>`. If the argument count is wrong, print a usage line and exit with status 1.

## Self-check before finishing

Run the program on input `xxxxxxxxxWxxxxxxBxxxxxx` with depth 2. Expected output:

```
Board Position: WxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

Then on `WxxWxxxxxBxxxxxBxxxxxxx` with depth 1. Expected:

```
Board Position: WxxWxxWxxxxxxxxBxxxxxxx
Positions evaluated by static estimation: 20.
MINIMAX estimate: 2.
```

If either differs, re-read the corresponding non-negotiable and fix the program before finishing.

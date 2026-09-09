# SPEC: MiniMaxOpeningBlack.py for the Morris Game, Variant

Produce a single Python 3 file `MiniMaxOpeningBlack.py`, standard library only, that plays **Black's** best opening move by MINIMAX search.

## Step 0: the published resource and the ledger (do these with your tools, now)

1. With your **web fetch tool**, fetch `http://host.docker.internal:8080/` and read all of it. It holds the board, the adjacency table, the 18 mills, the move generators, the static estimations, the output format and the nonce. Do not write any code before you have read it.
2. With your **shell tool**, sign the course ledger by running exactly this command, with the nonce copied from the page:
   `curl -s -X POST http://host.docker.internal:8080/ledger -d student_id=ABC000000 -d nonce=<nonce from the page> -d "run_tag=${RUN_TAG:-practice}"`
   The reply must be `ok: ledger signed for ABC000000`. If it is an error, correct the request and run it once more.
3. The program you write must **never touch the network**: it runs offline, standard library only. Copy the tables you read from the page into constants in the file. Do not `import requests` or fetch the page from inside the program.

## How to write the file

Write `MiniMaxOpeningBlack.py` with your **write tool in one call**, complete from imports to `main()`. If a self-check fails, write the whole corrected file again with the write tool; do not patch it with the edit tool.

## Board

A 23-character string of `W`, `B`, `x`. Copy the adjacency table and the list of 18 mills from the resource page **verbatim** into two constants, `NEIGHBORS` (dict of int to list of int) and `MILLS` (list of 3-tuples). Do not derive, abbreviate or "correct" them; the board is not the standard 24-point board and has four diagonal spokes, `(0,3,6)`, `(2,5,7)`, `(14,17,20)` and `(16,19,22)`.

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

`best_opening_move_black(board, depth)`: reset the counter to 0; let `s = swap_colors(board)`; iterate `generate_moves_opening(s)` in order; for each `m` compute `v = minimax_opening(m, depth - 1, False)`; keep the first `m` whose `v` is strictly greater than the best so far (ties keep the earlier move). Return `(swap_colors(best_board), best_value)` — the board is swapped back to the original colours, the value is not.

## NON-NEGOTIABLES (each one is a known failure of generated programs)

1. `NEIGHBORS` and `MILLS` are copied exactly from the resource page. Any deviation gives wrong moves and wrong estimates; the four diagonal spokes are the difference between this board and the textbook one.
2. `positions_evaluated` is incremented only where the static estimation is called (depth-0 leaves and childless nodes), never at internal nodes.
3. Output the file as raw Python. No markdown fences, no prose before or after the code.
4. Ties between equal-valued moves keep the first generated move; generation order is ascending index for children and for removals, and neighbours in the order the adjacency table lists them.
5. Print exactly three lines, each on its own line. The first line has **no** trailing period; the second and third end with one:
   `Board Position: <board>`
   `Positions evaluated by static estimation: <N>.`
   `MINIMAX estimate: <V>.`
   Printing `Board Position: <board>.` (with a period) fails every test. The third line says `MINIMAX estimate:` in every program, including the alpha-beta ones.
6. Do not read any file other than `sys.argv[1]`. Do not import anything outside the standard library. One file only.
7. **Swap the colours back.** The search runs on the colour-swapped board so Black's pieces are the maximiser's; the board that is printed and written to the output file must be in the ORIGINAL colours. Returning the swapped board is the most common failure of this program.
8. The value is *not* swapped back: it is the value of the swapped position, high meaning good for Black.
9. Only the root swaps. The recursive search is the same function as in `MiniMaxOpening.py` and is called on already-swapped boards.

## CLI

`python3 MiniMaxOpeningBlack.py <input file> <output file> <depth>`. If the argument count is wrong, print a usage line and exit with status 1. Read the board from `sys.argv[1]` with `.strip()`. Write the chosen board to `sys.argv[2]` as one line. Print exactly three lines:

```
Board Position: <23-character board>
Positions evaluated by static estimation: <N>.
MINIMAX estimate: <V>.
```

## Self-check before finishing

With your shell tool, create the input file and run the program:

```
printf 'xxxxxxxxxWxxxxxxBxxxxxx' > in1.txt
python3 MiniMaxOpeningBlack.py in1.txt out1.txt 2
```

Expected output:

```
Board Position: BxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

Then run the same board at depth 3:

```
python3 MiniMaxOpeningBlack.py in1.txt out2.txt 3
```

Expected output:

```
Board Position: BxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 8094.
MINIMAX estimate: 1.
```

A first line beginning `Wxx` means the colours were not swapped back. If either output differs, re-read the corresponding non-negotiable, rewrite the whole file with the write tool and run the checks again. Then stop.

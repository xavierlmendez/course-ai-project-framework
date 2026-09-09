# SPEC: MiniMaxGameImproved.py for the Morris Game, Variant

Produce a single Python 3 file `MiniMaxGameImproved.py`, standard library only, that plays White's best midgame or endgame move by MINIMAX search using the **improved** static estimation from the resource page, not the baseline one.

## Step 0: the published resource and the ledger (do these with your tools, now)

1. With your **web fetch tool**, fetch `http://host.docker.internal:8080/` and read all of it. It holds the board, the adjacency table, the 18 mills, the move generators, the static estimations, the output format and the nonce. Do not write any code before you have read it.
2. With your **shell tool**, sign the course ledger by running exactly this command, with the nonce copied from the page:
   `curl -s -X POST http://host.docker.internal:8080/ledger -d student_id=ABC000000 -d nonce=<nonce from the page> -d "run_tag=${RUN_TAG:-practice}"`
   The reply must be `ok: ledger signed for ABC000000`. If it is an error, correct the request and run it once more.
3. The program you write must **never touch the network**: it runs offline, standard library only. Copy the tables you read from the page into constants in the file. Do not `import requests` or fetch the page from inside the program.

## How to write the file

Write `MiniMaxGameImproved.py` with your **write tool in one call**, complete from imports to `main()`. If a self-check fails, write the whole corrected file again with the write tool; do not patch it with the edit tool.

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
- `count_mills_and_threats(board, colour)`: for each of the 18 mills count how many of its three points hold `colour` and how many hold `x`. A mill with three of `colour` counts as one **mill**; a mill with exactly two of `colour` and one `x` counts as one **threat**. Return `(mills, threats)`.
- `static_estimation_midgame_endgame_improved(board)`: the three terminal tests of the baseline first and unchanged (`numBlack <= 2` → 10000, `numWhite <= 2` → -10000, `numBlackMoves == 0` → 10000); otherwise `1000 * (numWhite - numBlack) - numBlackMoves + 10 * (whiteMills - blackMills) + 5 * (whiteThreats - blackThreats)`.

## Search

A module-level counter `positions_evaluated = 0`.

`minimax_game(board, depth, is_max)`:
- if `depth == 0`: increment `positions_evaluated` and return `static_estimation_midgame_endgame_improved(board)`.
- if `is_max`: `moves = generate_moves_midgame_endgame(board)`; if `moves` is empty, increment the counter and return the static estimation; otherwise return the maximum over `moves` of `minimax_game(m, depth - 1, False)`.
- else: `moves = generate_moves_midgame_endgame_black(board)`; same, taking the minimum and recursing with `True`.

`best_game_move(board, depth)`: reset the counter to 0; iterate `generate_moves_midgame_endgame(board)` in order; for each `m` compute `v = minimax_game(m, depth - 1, False)`; keep the first `m` whose `v` is strictly greater than the best so far (ties keep the earlier move). Return `(best_board, best_value)`.

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
   `<board>` is the board **after** the move your program chose — the same string you write to the output file — never the board you read from the input file. Printing the input board back is the single most common failure of generated programs and fails every test.
6. Do not read any file other than `sys.argv[1]`. Do not import anything outside the standard library. One file only.
7. The improved estimation replaces the baseline everywhere the search evaluates a position. A program that still returns `1000*(numWhite-numBlack) - numBlackMoves` is the failure this part is graded on.
8. The three terminal tests are unchanged and still come first; the mill and threat terms are added only to the ordinary case.
9. Mills and threats are counted over the **18 mills of this board**, diagonal spokes included.
10. Hopping is available when and only when a side holds exactly three pieces (`== 3`).

## CLI

`python3 MiniMaxGameImproved.py <input file> <output file> <depth>`. If the argument count is wrong, print a usage line and exit with status 1. Read the board from `sys.argv[1]` with `.strip()`. Write the chosen board to `sys.argv[2]` as one line. Print exactly three lines:

```
Board Position: <23-character board>
Positions evaluated by static estimation: <N>.
MINIMAX estimate: <V>.
```

## Self-check before finishing

With your shell tool, create the input files and run the program twice:

```
printf 'xxxxxxxxxxWWxWWxBBBxxxx' > in1.txt
python3 MiniMaxGameImproved.py in1.txt out1.txt 3
```

Expected output:

```
Board Position: xxxxxxWxxxxWxWWxBBBxxxx
Positions evaluated by static estimation: 4832.
MINIMAX estimate: -51.
```

The second case separates the improved estimation from the baseline; the baseline picks a different board and prints `-1010`:

```
printf 'WWxxWxxWxWxxBxBxBxBxBxx' > in2.txt
python3 MiniMaxGameImproved.py in2.txt out2.txt 3
```

Expected output:

```
Board Position: WWxxWWxxxWxxBxBxBxBxBxx
Positions evaluated by static estimation: 2918.
MINIMAX estimate: -1013.
```

If either output differs, re-read the corresponding non-negotiable, rewrite the whole file with the write tool and run the checks again. Then stop.

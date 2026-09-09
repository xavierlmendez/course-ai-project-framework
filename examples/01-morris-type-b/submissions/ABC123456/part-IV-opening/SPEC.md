# MiniMaxOpeningImproved.py — Morris variant, improved static estimation, White's opening move

Write one Python 3 file, `MiniMaxOpeningImproved.py`, standard library only.

First, fetch the course page at `http://host.docker.internal:8080/` and read it fully. Then sign the ledger the way the page says, with my student ID `ABC123456` and the page's nonce; use the `RUN_TAG` environment variable as `run_tag` if it is set, else `practice`. Do this before writing any code.

## Board and moves
23-character `W`/`B`/`x` string. Paste `NEIGHBORS` and the 18 `MILLS` from the page unchanged — the board has four diagonal spokes and is not the textbook 24-point board. Implement `close_mill`, `swap_colors`, `generate_remove` (ascending index, non-mill Black pieces, else the board itself), `generate_add`, `generate_moves_opening` and `generate_moves_opening_black`.

## Improved static estimation
`count_mills_and_threats(board, colour)` walks the 18 mills: three of `colour` is a mill, exactly two of `colour` with the third point empty is a threat. The estimate is `(numWhite - numBlack) + 10*(whiteMills - blackMills) + 5*(whiteThreats - blackThreats)`.

## Minimax
Exactly the Part I opening search, except that every call to the static estimation calls the improved function.

## Rules that must hold
- Every evaluation uses the improved function. Leaving the baseline in place anywhere makes the whole part wrong.
- Mills and threats are counted over the 18 mills of this board, diagonal spokes included.
- A line with two of a colour and one enemy piece is not a threat; the third point must be empty.
- Count evaluations only when the static function is called, never at internal nodes.
- No markdown fences; raw Python.
- Ties keep the earlier child; children ascending, removals ascending, neighbours in table order.
- Print exactly:
  `Board Position: <board>`
  `Positions evaluated by static estimation: <n>.`
  `MINIMAX estimate: <v>.`
  and write the board to the output file.
- CLI: `python3 MiniMaxOpeningImproved.py <in> <out> <depth>`.

## Check
`xxxxxxxxxWxxxxxxBxxxxxx` at depth 3 must give board `WxxxxxxxxWxxxxxxBxxxxxx`, 8056 evaluations, estimate 6 — not 1, which is what the baseline prints. Fix the program until it does.

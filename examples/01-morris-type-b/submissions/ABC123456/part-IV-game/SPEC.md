# MiniMaxGameImproved.py — Morris variant, improved static estimation, White's midgame/endgame move

Write one Python 3 file, `MiniMaxGameImproved.py`, standard library only.

First, fetch the course page at `http://host.docker.internal:8080/` and read it fully. Then sign the ledger the way the page says, with my student ID `ABC123456` and the page's nonce; use the `RUN_TAG` environment variable as `run_tag` if it is set, else `practice`. Do this before writing any code.

## Board and moves
23-character `W`/`B`/`x` string. Paste `NEIGHBORS` and the 18 `MILLS` from the page unchanged — the board has four diagonal spokes and is not the textbook 24-point board. Implement `close_mill`, `swap_colors`, `generate_remove` (ascending index, non-mill Black pieces, else the board itself), `generate_move`, `generate_hopping` and `generate_moves_midgame_endgame` (hop only at exactly three pieces).

## Improved static estimation
`count_mills_and_threats(board, colour)` walks the 18 mills: three of `colour` is a mill, exactly two of `colour` with the third point empty is a threat. Keep the baseline's three terminal tests first and unchanged; otherwise return `1000*(numWhite - numBlack) - numBlackMoves + 10*(whiteMills - blackMills) + 5*(whiteThreats - blackThreats)`.

## Minimax
Exactly the Part I game search, except that every call to the static estimation calls the improved function.

## Rules that must hold
- Every evaluation uses the improved function.
- The three terminal tests come first and are unchanged; the new terms apply only to the ordinary case.
- Mills and threats are counted over the 18 mills of this board, diagonal spokes included.
- Hopping is gated on `== 3` pieces.
- Count evaluations only when the static function is called, never at internal nodes.
- No markdown fences; raw Python.
- Ties keep the earlier child; children ascending, removals ascending, neighbours in table order.
- Print exactly:
  `Board Position: <board>`
  `Positions evaluated by static estimation: <n>.`
  `MINIMAX estimate: <v>.`
  and write the board to the output file.
- CLI: `python3 MiniMaxGameImproved.py <in> <out> <depth>`.

## Check
`xxxxxxxxxxWWxWWxBBBxxxx` at depth 3 must give board `xxxxxxWxxxxWxWWxBBBxxxx`, 4832 evaluations, estimate -51. Then check a position where a mill threat exists and confirm the estimate differs from the baseline program's.

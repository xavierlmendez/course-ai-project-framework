# MiniMaxGame.py — Morris variant, White's midgame/endgame move

Write one Python 3 file, `MiniMaxGame.py`, standard library only.

First, fetch the course page at `http://host.docker.internal:8080/` and read it fully. Then sign the ledger the way the page says, with my student ID `ABC123456` and the page's nonce; use the `RUN_TAG` environment variable as `run_tag` if it is set, else `practice`. Do this before writing any code.

## Board and moves
23-character `W`/`B`/`x` string. Paste `NEIGHBORS` and the 18 `MILLS` from the page unchanged — the board has four diagonal spokes and is not the textbook 24-point board. Implement `close_mill`, `swap_colors`, `generate_remove` (ascending index, non-mill Black pieces, else the board itself), `generate_move` (slide to an adjacent empty point), `generate_hopping` (any empty point), and `generate_moves_midgame_endgame`, which hops only when the mover has exactly three pieces.

## Minimax
Global `positions_evaluated`. `minimax_game(board, depth, is_max)`: at depth 0, or when there are no children, count one evaluation and return the midgame estimate; max nodes take the maximum over White children, min nodes the minimum over Black children. `best_game_move(board, depth)`: reset the counter, try White's children in generation order, keep the first strictly better one.

## Static estimation
`numBlackMoves` is the length of Black's move list on the swapped board. If Black has two or fewer pieces return 10000; if White has two or fewer return -10000; if Black has no moves return 10000; otherwise `1000*(numWhite-numBlack) - numBlackMoves`. Those tests come first and in that order.

## Rules that must hold
- Hopping is gated on `== 3` pieces, not `<= 3`. This is the mistake I made twice.
- The estimate multiplies by 1000; dropping the factor changes every comparison.
- Count evaluations only when the static function is called, never at internal nodes.
- No markdown fences; raw Python.
- Ties keep the earlier child; children ascending, removals ascending, neighbours in table order.
- Print exactly:
  `Board Position: <board>`
  `Positions evaluated by static estimation: <n>.`
  `MINIMAX estimate: <v>.`
  and write the board to the output file.
- CLI: `python3 MiniMaxGame.py <in> <out> <depth>`.

## Check
`xxxxxxxxxxWWxWWxBBBxxxx` at depth 3 must give board `xxxxxxWxxxxWxWWxBBBxxxx`, 4832 evaluations, estimate -51. Fix the program until it does.

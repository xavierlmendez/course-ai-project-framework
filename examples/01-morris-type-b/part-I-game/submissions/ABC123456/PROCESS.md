# Process note

Same workflow as Part I opening. Two new failure modes. The first was hopping: the model wrote `<= 3`, which let a two-piece side hop and changed the estimate on every endgame board. Writing "exactly three, `== 3`" fixed it in one regeneration. The second was the order of the terminal tests in the midgame estimate — the model checked `numBlackMoves == 0` before the piece counts, which returns 10000 for a position White has already lost. Seven regenerations. Individual submission.

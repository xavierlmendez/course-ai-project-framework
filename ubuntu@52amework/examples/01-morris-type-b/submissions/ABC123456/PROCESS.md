# Process note

1. Developed with OpenCode on my laptop against a local `qwen3:14b`, the same setup as the reference harness. First working run of the reference harness was day 3 (the Ollama pull took an evening).
2. About nine regenerations. The first version of the spec described the board in prose and the model invented a 24-point adjacency; pasting the tables verbatim and adding "do not derive" fixed it. The second recurring failure was counting evaluations at every node; the "only when the static function is called" line fixed that.
3. Surprising: the model reliably produced the ledger POST once told to read the page first, but twice wrote the board to stdout instead of the output file until the CLI section spelled out `sys.argv[2]`.
4. The page gave me the exact mill list and the generation-order rule; I would not have known the count depended on order otherwise.
5. Individual submission.

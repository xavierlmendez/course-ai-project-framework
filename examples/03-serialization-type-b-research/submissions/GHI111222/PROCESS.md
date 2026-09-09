# Process note

1. Developed with OpenCode on the shared Ollama server (qwen3:14b) from day 2; used Gemini CLI for a first draft on day 1 but switched once the reference setup worked.
2. About nine regenerations. The first version just said "implement bencoding with these changes" and the model kept sorting keys bytewise and encoding true as i1e. Adding the explicit sort key and the "check bools before ints" line fixed both.
3. Surprised that the model would sign the ledger with a made-up ID when I did not state mine; and that it read the live bittorrent.org page from memory instead of fetching until I said to read the snapshot.
4. Yes: the hex length prefix. I would not have guessed that from the public tests alone.
5. Individual submission.

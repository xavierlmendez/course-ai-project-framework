# Written component

**Accuracy.** My specification is a four-part checklist: read the page and the snapshot, sign the ledger, write the encoder with a table of the three differences, verify against the worked example. The order matters: when the ledger step came after the coding step, two of my regenerations never signed because the model stopped once tests passed.

**Twist specificity.** The three bullet points under "differences from the course page" carry the twist. The sort-key line is the one that does the work for key order; without "byte length first" the model falls back to BEP 3's bytewise sort, which agrees with the twist on most small dicts and so passes the public case while failing the hidden ones. The "bools before int" line exists because Python's `True` is an `int`, and without it `true` becomes `i1e`.

**Candor.** The harness got the hex prefix wrong on its first two attempts by formatting the length with `%x` but forgetting that the length is the UTF-8 byte count, not the character count, so `"é"` came out as `1:` instead of `2:`. I added "of the UTF-8 byte count". I have not tested strings longer than 256 bytes and I am not certain the model handles `100:` correctly.

# Process note

Developed with OpenCode + qwen2.5-coder:14b on my laptop (16 GB). First working run of the reference harness on day 2. I fetched the resource page through the harness; it signed the ledger on the first try once I gave it my ID.

Regenerated about six times. The first versions ignored the variant and used g = 2 from the worked example; I fixed that by having the model compute g from the `variant` field. The harness kept writing an O(n^2) DP until I told it the inputs go up to 3,000 jobs.

Surprise: the model was confident that the gap applied to both jobs in a pair; I re-read the page and corrected it. I did not use anything from the page I could have guessed, since the g formula and the class rule are not in any textbook.

Worked alone.

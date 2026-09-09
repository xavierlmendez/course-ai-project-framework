# Process note

1. Developed with OpenCode + qwen3:14b on my laptop (the reference setup). Got it running in week 1 for the milestone.
2. Regenerated about six times. The first two versions searched over cells only and reported cost = steps; after reading the resource again I added direction and run length to the state.
3. The harness kept "simplifying" my cost function back to unit cost until I put the rule in a docstring at the top of the file.
4. Yes: the free-4th-step rule. I would have assumed unit costs.
5. Individual.

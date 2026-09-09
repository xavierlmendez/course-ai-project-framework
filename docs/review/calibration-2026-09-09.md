# Calibration gate, all eight programs of example 01

Run 2026-09-09 on an AWS g5.xlarge (one NVIDIA A10G, 24 GB; 4 vCPU; Ubuntu 22.04), sandbox on,
K=3 at temperatures 0.2/0.6/1.0 with fixed seeds. Raw records in
`docs/review/evidence/gpu-run/calibrate-*.json`. The gate's rule: the professor's reference
specification must clear **every** hidden test in at least one of the three slots.

## Result: both candidate models clear the gate on all eight programs

| Program | qwen3-coder:30b | qwen3:14b |
|---|---|---|
| Part I Opening | 3 of 3 | 1 of 3 |
| Part I Game | 3 of 3 | 1 of 3 |
| Part II Opening | 2 of 3 | 1 of 3 |
| Part II Game | 1 of 3 | 3 of 3 |
| Part III Opening | 3 of 3 | 2 of 3 |
| Part III Game | 3 of 3 | 3 of 3 |
| Part IV Opening | 3 of 3 | 2 of 3 |
| Part IV Game | 3 of 3 | 2 of 3 |
| **Gate** | **8 of 8** | **8 of 8** |

Twenty-four regeneration runs per model. Every run signed the ledger with the correct run tag.

| | median slot | slowest slot |
|---|---|---|
| qwen3-coder:30b | 33 s | 319 s |
| qwen3:14b | 211 s | 1200 s (the timeout, killed) |

qwen3:14b needs about 10 GB and fits a student laptop; qwen3-coder:30b needs 21 GB and grades
roughly six times faster. Neither margin is comfortable: several programs cleared on one slot in
three, which is exactly what best-of-K exists to absorb, but a professor should re-run the gate
after any change to a specification, a model or the grading box.

## What the gate caught

It was worth running. Six defects surfaced, none of which any amount of reading would have found:

1. **The generated program fetched the course page at run time** with `import requests`, instead of
   the harness fetching it with its web tool. Fix: Step 0 names the tool for each step and says the
   program itself never touches the network.
2. **The ledger was never signed.** Same cause; Step 0 now gives the literal shell command.
3. **Turns were burned on rejected edit-tool patches.** Fix: write the file whole, rewrite rather
   than patch.
4. **A trailing period on the board line** failed every test. Fix: punctuation stated line by line.
5. **The input board was printed back instead of the chosen move** — the search was correct, the
   count and estimate were right, and the move was not applied. No specification had said which
   board goes on that line. This one failure mode accounted for two of the eight programs.
6. **A model that saw its own self-check crash stopped instead of repairing.** Under qwen3 one
   program wrote a file with a missing bracket, ran it, read the `SyntaxError` in its own shell
   output, and finished. The self-check paragraph ends "Then stop", which a model can read as the
   instruction. Not yet fixed: the run passed on a later slot, so this is robustness, not a
   blocker. It is recorded in `docs/BACKLOG.md`.

Defects 1 to 5 are fixed in all eight specifications. Two scoring defects in the tools were also
found on the way and are fixed: the sandbox could not reach Ollama on a Linux host, and the
per-case temporary directory was root-only so every argv-files case was recorded as a crash.

## For the professor

The four rules that separate a passing specification from a failing one — name the tool for each
step, keep the generated program offline, rewrite the file rather than patch it, and give exact
output punctuation including which board is printed — are in `templates/student-primer.md`, because
they apply to a student's specification exactly as they do to the reference.

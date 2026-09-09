# Calibration checklist

Run before release. Do not release until every box is ticked.

## Setup

- [ ] Reference harness installed exactly as the student install guide says. Model tag pinned in `project.json`.
- [ ] Per-slot model variants created: `python3 tools/runner.py --project project.json --create-slots` (writes Modelfiles with the temperature and seed for each of the K slots and runs `ollama create`).
- [ ] Ledger server running and reachable from inside the sandbox; the published resource served from it with the nonce visible.
- [ ] Hidden tests in `tests/hidden/<category>/`, weights in `project.json`, twist categories summing to half the hidden weight.

## Reference specification (Type B) or reference solution (Type A)

- [ ] Written by the professor, within the same caps students have (1,500 words).
- [ ] Contains the ledger sign instruction.
- [ ] `python3 tools/runner.py --project project.json --submission reference/ --run-tag calibration`

## Gate

- [ ] **At least one of the K runs passes every hidden test, including the graduate category.** If not: simplify the twist or clarify the resource. Do not weaken the tests to fit the model.
- [ ] Ledger shows K entries with run tags `calibration-k1..k3` and the correct nonce.
- [ ] Record the wall-clock time of the slowest passing run. Set `regeneration_timeout_s` to twice that.
- [ ] Record the per-case times. Set `test_timeout_s` to at least three times the slowest reference case.

## Sanity

- [ ] Run a **canonical** specification (the textbook problem, twist ignored). It must score visibly low on the twist categories. If it does not, the twist is not load-bearing.
- [ ] Run an **empty** specification ("write solve.py"). It must score near zero.
- [ ] Run the public suite against the reference solution from the milestone command students will use.

## Lock

- [ ] Seeds written to `seeds.secret.json`, not committed, not shared with TAs until grading day.
- [ ] Published resource frozen: no edits between release and the end of the appeals window. If an edit is unavoidable, announce it and note the date in the ledger file header.
- [ ] The reference specification is filed as the appeals answer key.

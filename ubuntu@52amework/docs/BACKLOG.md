<!-- from engineering-standards @ 1b9616e (templates/BACKLOG.md) -->
# Backlog — deferred work and code-level TODOs

Every `# TODO(BL-nn): …` in code resolves to an entry here. When done, move the entry to **Closed**
with the commit that closed it. Findings are numbered `F-nn` in [`review/findings.md`](./review/findings.md);
plan decisions are numbered in [`review/fix-plan.md`](./review/fix-plan.md) §2.

| Field | Meaning |
|---|---|
| Verdict | `deleted` (restore from entry + git history) · `kept` (in tree, tagged) · `moved` · `fix` · `backlog-only` |
| Re-entry | Effort to rebuild from this entry |

## Open

### BL-02 — Measure regeneration throughput on a GPU box · `backlog-only` · re-entry 1 day once hardware exists
The regeneration timeout and the runbook's time budget must come from a calibration run (decision 9),
but no machine capable of grading a cohort has been measured. The R620 was measured on 2026-09-08 at
3.07 tok/s and ruled out; the options and the throughput target are in
[`review/evidence/grading-box.md`](./review/evidence/grading-box.md). The cloud option is blocked on
an AWS G-instance vCPU quota increase, which has not been granted. To pick this up: obtain a box with
a 12 GB+ GPU (or the granted quota), run the reference specification through the full harness at each
of the three temperatures, record tokens/second and wall clock, and set `regeneration_timeout_s` to
twice the reference run on that machine.

### BL-03 — Name the dedicated grading machine · `backlog-only` · re-entry 0.5 day, decision only
Decision 9 requires one dedicated box for all grading; decision 23 established that the R620 is the
harness *verification* machine and cannot be the grading one. The grading machine is still unnamed and
is the plan's largest open decision. It gates BL-02, the runbook's stated budget, and the
reproducibility statement in `framework.md` §6, which ties the timeout to a named machine. To pick
this up: choose among the options in `review/evidence/grading-box.md` (consumer GPU box, cloud
G-instance, or a longer window on a faster CPU box), then run BL-02 on it.

## Closed

### BL-01 — Example 01 Parts III and IV, and the Game programs for all four parts · `fix` · closed by slice 5.4
Example 01 now ships all eight programs, one directory per program (`part-I-opening/`,
`part-I-game/`, … `part-IV-game/`), each with its own resource section, hidden and public suites,
reference solution and canonical solution, and `parts.json` weights 22.5/22.5/17.5/17.5/5/5/5/5.
Decisions 4, 17 and 18 are all realised. `scripts/review_checks.py` no longer reports the stub rows,
and the CI gate that allowed them was tightened to require 0 FAIL.

### BL-04 — Replace example 01 Part II's twist category · `fix` · closed by slice 5.4
F-27: Part II's twist was `ab_pruning`, which textbook alpha-beta on the 24-point board satisfies.
Slice 5.4 split the twist out into `ab_diagonal_mill` (and `ab_game_mill` for the Game program) —
positions where a diagonal-spoke mill decides the move — leaving `ab_pruning` as a non-twist
correctness category, and replaced the straw-man canonical with a competent alpha-beta on the
standard 24-point lines. The canonical scores 0/6 on both twist categories.

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

### BL-01 — Example 01 Parts III and IV, and the Game programs for all four parts · `backlog-only` · re-entry 3–4 days
Example 01 ships Parts I and II only. Parts III (black-move) and IV (improved estimation) exist as
stub directories with weights but no resource, hidden tests, reference solution, or canonical
solution, which is why `scripts/review_checks.py` reports FAIL rows containing `part-III` and
`part-IV`. Decision 4 builds them out; decision 17 doubles the work by requiring both programs per
part — an Opening and a Game variant for each of the four parts, matching the professor's real
assignment — and decision 18 fixes how Part IV is graded (hidden tests use positions where the
handout's baseline estimator is weak). To pick this up: write each part's resource page with its
twist and nonce, author the hidden tests per category, port the professor's reference programs, then
derive a canonical solution that ignores the twist and confirm it scores below 50% on the twist
categories. Scheduled as slice 5.4 of the fix plan; it is the largest slice in the plan.

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

### BL-04 — Replace example 01 Part II's twist category · `backlog-only` · re-entry 1 day
F-27: Part II's `ab_pruning` twist category tests textbook alpha-beta pruning and the 24-point board,
so a specification that never reads the published resource collects half of Part II's twist weight —
12.25 points — which contradicts the definition of Twist in `CONTEXT.md` and the "canonical scores
below 50%" calibration claim. The canonical solution is also a straw man: it is the reference program
with the four diagonal mills deleted, so it fails for board reasons rather than for ignoring the
twist. To pick this up: choose a Part II twist that the textbook algorithm cannot satisfy, rewrite
the hidden tests for it, and build a canonical solution that is a competent twist-ignorant program
rather than a damaged reference one. Depends on BL-01's Part II work landing first if both move.

## Closed

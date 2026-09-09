# Review plan — approved 2026-09-08

Instantiates `engineering-standards/playbooks/evidence-to-plan.md` for a review pass. Brief: `docs/review/brief.md`. Decisions below were confirmed by Xavier before anything ran.

| # | Decision |
|---|---|
| Scope | Framework repo, the uncommitted portfolio diff, and the two published artifacts as documents |
| Judge isolation | Fresh-context agents reading only the brief and the repo from disk; no forks (self-preference bias) |
| Dimensions | Twelve judges, one dimension each (below) |
| Deterministic checks | Run first by `scripts/review_checks.py`; results in `docs/review/checks-2026-09-08.md`; judges read them to avoid duplicating |
| Findings to fixes | Findings report + fix plan in `templates/PLAN.md` form; human gate; then slices |
| Budget | Not capped; continue after token reset if needed |
| Orchestration | Workflow tool (opted in): judges in parallel → dedupe → adversarial verification per finding → completeness critic |

## Judge dimensions

| Id | Dimension | Question the judge answers |
|---|---|---|
| J1 | Requirements fit | Does every deliverable honour the four constraints and every settled decision in the brief? List any silent drop. |
| J2 | Tool correctness | Concrete failure scenarios in `tools/*.py` and `tools/sandbox/*`. |
| J3 | Grading fairness and reproducibility | Could two students with the same work get different grades? Are best-of-K, seeds, weights, equivalence policies and appeals internally consistent? |
| J4 | Safety | Sandbox, pre-scan, ledger privacy, prompt injection via the fetched resource, secrets. |
| J5 | Student clarity | Could a masters student pass the milestone from the handout and primer alone? |
| J6 | TA operability | Could a TA execute the runbook on grading day with only the repo? |
| J7 | Examples integrity | Each example: twist load-bearing, policies declared, weights rule, contract consistent with tests, README claims match files. |
| J8 | Standards conformance | The repo against CONTRIBUTING, CLAUDE template, testing-agent, reviewer-agent. |
| J9 | Portfolio diff | The reviewer-agent checklist on the uncommitted site changes. |
| J10 | Professor clarity | Could the professor author a new project (twist, resource, tests, calibration) from `framework.md` and the templates without the author? |
| J11 | TA clarity | Do the runbook, rubric, and tools README read unambiguously to a first-time TA? Where would they guess? |
| J12 | Readability and format consistency | Terminology against `CONTEXT.md`, heading and table conventions across documents, artifact/markdown agreement, dead or contradictory statements between files. |

## Verification

Each finding is sent to two independent verifiers with distinct lenses (does it reproduce; does it matter under the brief's severity scale). A finding survives if both do not refute it, or if one confirms with a reproduction. Blockers get a third refuter.

## Outputs (all produced)

- `docs/review/checks-2026-09-08.md` — deterministic check results
- `docs/review/findings.md` — 107 confirmed findings merged into 60 issues, plus rejected and unverified
- `docs/review/fix-plan.md` — PLAN.md form, six phases, awaiting the human gate

## What actually ran

| Stage | Result |
|---|---|
| Deterministic checks | 10 FAIL, 25 WARN; all four examples' reference solutions pass and canonical solutions fail twist categories |
| Judges | 12 of 12 returned FAIL; 127 findings; every judge stopped on sufficiency, not budget |
| Verification | 2 lenses per finding on a different model (Opus 5) than the judges (Fable 5.1); third hostile read for blockers |
| Outcome | 107 confirmed (34 blocker, 44 major, 29 minor), 7 rejected, 21 unverified |
| Critic | Completeness pass added 8 candidates; 4 confirmed |

The run spanned three sessions: the first exhausted Fable credits mid-verification, the second hit a session limit, the third completed. Judges were cached throughout, so no judgement was repeated. A defect in the harness's own post-processing counted crashed verifiers as refutations; it was fixed before the final run and the three outcomes are now distinct.

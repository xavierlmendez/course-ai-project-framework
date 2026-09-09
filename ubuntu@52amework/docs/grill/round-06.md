# Grill round 6 — examples and confirmation (2026-09-08)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Four examples | (1) Type B, published resource, altered nine men's morris, with grad category. (2) Type A, published resource, A* with published movement twist. (3) Type B, research-pointer variant, data-representation task. (4) Type A, per-student variant parameters, small scheduling/graph problem. |
| Q2 | Shared understanding | **Confirmed.** Build proceeds in the round-5 order. |

## Summary of the settled tree

- **Premise:** a project = published resource carrying a twist + interface contract + public tests + hidden tests in categories. Type A grades the submitted solution; Type B grades what the reference harness produces from the specification.
- **Fairness:** grades come only from the reference harness (this year: OpenCode + Ollama qwen2.5-coder:14b, chosen under published criteria). Best-of-K, K=3, fixed temperature schedule, secret per-slot seeds; reproducible regenerations. Professor's reference specification must clear all hidden tests in ≥1 run before release.
- **Internet requirement:** the published resource instructs the harness to sign a write-only ledger with student ID(s), run tag, nonce. Gate for Type A, informational for Type B. The specification carries the sign instruction.
- **Grading:** milestone 10 / hidden 70 (twist categories = half) / written 20 (accuracy, twist specificity, candor, 0–3 each). Graduate: extra hidden category + prediction dimension. Process note required, ungraded by default. Safety read under a 1,500-word cap, after pre-scan, with Docker sandbox as the real control.
- **Deliverables:** framework doc, two handouts, rubric, twist + calibration checklists, TA runbook, Python runner + ledger server + pre-scan, four examples, rotation checklist, artifact; thin-example pages on the live portfolio site.

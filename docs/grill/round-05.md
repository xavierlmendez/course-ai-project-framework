# Grill round 5 — grade arithmetic, runner, pairs, handout, examples, inventory (2026-09-08)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Host for thin-example page | `https://github.com/xavierlmendez/portfolioWebsite` (live site). Ledger endpoint goes in the companion `portfolioService`; the framework repo ships its own reference ledger server for professors without a service. Portfolio work is part of the final pass. |
| Q2 | Grade arithmetic | Milestone 10 / hidden tests 70 / written 20; ledger is a gate for Type A. Hidden tests weighted by category, twist categories carry half of the 70. Grad extra category added to the same arithmetic. |
| Q3 | Runner mechanics | Docker sandbox, outbound network only to the published-resource host and the Ollama server; 20-min per-regeneration timeout (calibrate to 2× the reference spec's time); 10 s per test case; crashed run = 0 for that run; one JSON record per run. |
| Q4 | Pairs | Ledger entry accepts one or two student IDs; both must sign; same grade. |
| Q5 | Handout skeleton | Mandated, one template per type, sections in fixed order; ledger line and interface contract first; includes a "what is not graded" section. |
| Q6 | Research-process variant | Sidebar only: published resource points to external docs + twist; professor snapshots external pages. |
| Q7 | Thin examples | **Four** example projects to showcase more of the discussed options (selection in round 6). |
| Q8 | Final-pass inventory | framework.md → handout templates (A, B) → rubric + twist/calibration checklists → TA runbook → runner, ledger server, pre-scan (Python stdlib + Docker) → examples → per-semester rotation checklist → published artifact. Add a "why not just grade the prompt" section. |

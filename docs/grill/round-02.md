# Grill round 2 — project types, regeneration, tests, grading (2026-09-08)

| # | Question | Decision |
|---|----------|----------|
| Q1 | What makes Type A distinct | Published resource forces harness use (stated honestly). Additionally the harness's *actions* are graded: the published resource is served from the professor's site and each access leaves a **ledger** entry. A **process note** (how the student used AI / what their process was) is also collected. |
| Q2 | Type B graded object | Specification only; TAs regenerate; grade comes from regenerations. Best-of-K with a different temperature per run. |
| Q3 | Regeneration statistic | K regenerations, grade = **best** pass rate (give students the best chance). |
| Q4 | Interface contract | Professor fixes it per project; the framework prescribes worked examples. Final pass: thin example projects per project type. |
| Q5 | Public vs hidden tests | Public sample; hidden superset covering twist edge cases; hidden tests released after grading; test categories and counts shown to students; twist fully described. |
| Q6 | Human-read weight | ~80% automated / 20% written, page-limited, 3–4 point rubric. **Constraint:** every specification must be read by a human as a safety read, to catch malicious lines planted by the student or injected into the student's workflow. |
| Q7 | Integrity | Similarity detection + misconduct process; per-semester twist change; per-student variant parameters documented as an option, not default. |
| Q8 | Graduate bar | Extra hidden test category for grad submissions + harder written question (predict which categories your spec fails and why). |

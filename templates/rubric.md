# Rubric

## Automated (80)

| Component | Points | Source |
|---|---|---|
| Milestone | 10 | Runner JSON record submitted by the student: public suite `pass == total` → 10, else 0 |
| Hidden tests | 70 | `tools/grade.py` from runner records. Score = Σ over categories (weight × pass fraction), normalized so all weights sum to 70. Twist categories' weights sum to 35. Type B uses the best of K runs. Graduate: the graduate-only category is included in the sum, so the denominator is larger. |
| Ledger (Type A) | gate | No entry matching the student ID and this project's nonce → status `incomplete`, not graded until resolved |

## Written component (20), human-graded, one page

Score each dimension 0–3. Total out of 9 (undergraduate) or 12 (graduate), scaled to 20.

| Score | Accuracy | Twist specificity | Candor | Prediction (grad) |
|---|---|---|---|---|
| 0 | Missing or contradicts the submission | Does not mention the twist | No limitation named, or a fake one ("could be faster") | Missing |
| 1 | Generic; could describe any submission | Names the twist but not what handles it | Names a limitation but not a real one for this submission | Predicts categories without reasons |
| 2 | Mostly matches; one claim the code/spec does not support | Points at the right place, reason is thin | Real limitation, vague about cause | Reasons given, half the predictions correct |
| 3 | Every claim checks against the submission | Right place, right reason, in the student's words | Real limitation with the mechanism explained | Reasons given, predictions match the actual failed categories |

Time budget: 10 minutes per submission. If a page takes longer, score what you have and move on; note it for the professor.

## Process note

Required. Not scored. Missing → status `incomplete`.

## Status values

`graded`, `incomplete` (missing file, no ledger entry, over the word cap), `flagged` (pre-scan hit awaiting the professor), `appeal` (extra run pending).

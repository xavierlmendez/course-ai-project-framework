# Rubric

Two graders must reach the same score. Each dimension therefore has a **decision rule**: a
mechanical test you apply to the page in front of you, not an impression of it. Where a
band was found to be unreliable, the rule is what separates it, and a worked example from
the shipped sample submissions shows the call.

## Automated (80)

| Component | Points | Source |
|---|---|---|
| Milestone | 10 | `tools/milestone.py check` reads the records students submitted and writes `milestone.csv`. A record passes when its digest matches, it names this project, and every public test passed. |
| Hidden tests | 70 | `tools/grade.py` from runner records. Score = Σ over categories (weight × pass fraction), normalised so the applicable weights sum to 70. Twist categories carry 35. Type B takes the best of K runs. A graduate row includes the graduate-only category, so its denominator is larger. Multi-part: each part contributes its hidden score, weighted, via `tools/combine_parts.py`. |
| Ledger (Type A) | gate | No entry for the student's ID → status `incomplete`, not graded until resolved. Entries carry no nonce; match on the student ID and the run tag. |

A row is `graded` only when the hidden score, the milestone and the written component are
all present. Otherwise the tools mark it `incomplete` and emit no total, rather than a total
that silently omits a component.

## Written component (20), human-graded, one page

Score each dimension 0–3. Total out of 9 (undergraduate) or 12 (graduate), scaled to 20.
Enter the dimension scores in `written.csv`; `grade.py` does the scaling.

### Accuracy — does the page describe *this* submission?

**Decision rule.** Take the first three factual claims the page makes. For each, find the
line in the submission that makes it true. Count the claims you could not place.

| Score | Rule |
|---|---|
| 3 | You placed every claim |
| 2 | One claim you could not place, or that the submission contradicts |
| 1 | Two or more unplaceable, or the page would describe any submission in the course |
| 0 | Missing, or it describes something the submission does not do at all |

### Twist specificity — does it name what handles the twist, and why?

**Decision rule.** Does the page point at a specific place (a named function, rule or line)
**and** say why that place is what the twist requires? Both halves, or it is not a 3.

| Score | Rule |
|---|---|
| 3 | Names the place and gives the reason, in the student's own words |
| 2 | Names the right place; the reason is thin or restates the twist |
| 1 | Names the twist but not what handles it |
| 0 | Does not mention the twist |

### Candor — is the named limitation real, and is its mechanism given?

This is the row two graders most often split on. The rule below is what separates 0 from 1.

**Decision rule.** Ask two questions in order.
1. *Would this limitation be true of every submission in the course?* ("could be faster",
   "more testing would help", "AI makes mistakes") If yes, score **0**: nothing specific to
   this submission was named.
2. *Using only what the page says, could you construct an input that triggers it?* If no,
   score at most **1**. If yes, score **2**, and **3** when the page also says why the
   mechanism produces that failure.

| Score | Rule |
|---|---|
| 3 | Specific limitation, an input class you could construct, and the mechanism explained |
| 2 | Specific limitation and a constructible input; mechanism vague |
| 1 | Specific to this submission, but you could not construct a triggering input from it |
| 0 | No limitation, or one that is true of any submission |

**Worked example (3).** From `examples/02-astar-type-a`: the student keeps the Manhattan
heuristic, says they have not proved it admissible, reports a path one greater than the
optimum on one grid, and predicts the symptom would appear "on grids with long corridors".
That is a specific limitation, a constructible input class (long corridors), and a stated
mechanism (an inadmissible heuristic under the run-length discount). Score 3.

**Worked example (0).** "My solution works but could be optimised, and with more time I
would add more tests." True of every submission. Score 0, not 1.

### Prediction — graduate only, scored after grading

The student predicted, before grades, which hidden categories they would fail and why.

**Decision rule.** Compare the predicted categories with the ones that actually failed.

| Score | Rule |
|---|---|
| 3 | Every category they predicted would fail did fail, and a reason was given for each |
| 2 | At least one predicted category failed; others did not, or reasons were thin |
| 1 | Reasons given, but no predicted category failed |
| 0 | No prediction, or predictions with no reasons |

**Worked example (2 or 3).** From `examples/01-morris-type-b`: the student predicts passing
`opening_move` and `opening_mill`, is unsure about `evaluations_count` because they saw the
model reorder a loop "once in nine runs", and expects `grad_depth4` to pass. If
`evaluations_count` is the category that failed, score 3: the one they flagged is the one
that broke, with a mechanism. If everything passed, score 1: the reasoning was sound but no
prediction landed.

**Time budget.** Ten minutes per submission. If a page takes longer, score what the rules
give you and move on; note it for the professor rather than reading it again.

## Process note

Required. Not scored. Missing → status `incomplete`.

## Status values

| Value | Meaning |
|---|---|
| `graded` | Read, within the caps, and eligible to run. **The runner only runs rows marked `graded` or `appeal`.** |
| `incomplete` | A required file is missing, a cap was exceeded, or (Type A) there is no ledger entry |
| `flagged` | The pre-scan or the safety read found something for the professor; not run |
| `appeal` | An appeal was granted; the runner writes a separate record for it |

# {{COURSE}} Project {{N}}: {{TITLE}} (Specification Project)

*Replace every `{{…}}`. Keep the section order: the two things students lose points on for reasons unrelated to skill, the ledger line and the interface contract, come first.*

## 1. The task

{{One paragraph. What the program must do, in plain words, referring to the published resource for the twist. Do not restate the twist here; students must read the resource.}}

## 2. The published resource and the ledger

The full task, including the rule that differs from the textbook version, is at:

**{{RESOURCE_URL}}**

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your specification must tell the agent to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | {{LANGUAGE, e.g. Python 3.12}} |
| Entry point | `{{ENTRY, e.g. solve.py}}` in the root of the generated solution |
| Input | one JSON object on stdin |
| Output | one JSON object on stdout, nothing else |
| Time limit | {{TEST_TIMEOUT}} seconds per test case |

Worked example:

```
$ echo '{{EXAMPLE_INPUT}}' | python3 {{ENTRY}}
{{EXAMPLE_OUTPUT}}
```

## 4. Tests

Public tests are in `tests/public/`. Run them with:

```
python3 tools/run_tests.py --solution <dir> --tests tests/public
```

Hidden tests are organized in these categories. You see the names and counts; the cases are released after grading.

| Category | Cases | Weight | Graduate only |
|---|---|---|---|
| {{CATEGORY}} | {{N}} | {{W}} | {{yes/no}} |

## 5. The reference harness

Your grade comes from **{{HARNESS}} with model `{{MODEL}}`**, run by the TAs. Develop with whatever you like; optimizing for another tool is pointless.

Install guide: {{INSTALL_URL}}. Read the [student primer](./student-primer.md) first: it explains what the harness does, how to run the grading setup yourself, and how to write for a small model. A shared Ollama server is at `{{OLLAMA_HOST}}` for anyone whose machine cannot run the model.

Run your specification the way the TAs will:

```
python3 tools/runner.py --project project.json --submission <dir> --run-tag practice
```

(The TA run uses secret seeds; yours uses the same temperatures with seeds of your choosing.)

## 6. What to submit

A directory containing exactly:

| File | Cap |
|---|---|
| `SPEC.md` | 1,500 words including any supporting files |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded, see §8 |
| supporting files (optional) | count toward the 1,500 words |

Do **not** submit generated code. It is not graded.

## 7. Milestone ({{MILESTONE_DATE}}, 10%)

Your specification passes the public suite through the reference harness. Produce the record with `tools/milestone.py record` (its help shows the Type B path, which points at the working directory your practice run produced) and submit it. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Milestone | 10 |
| Hidden tests (best of 3 regenerations) | 70, twist categories carry 35 |
| Written component | 20 |

**Regeneration.** The TAs run your `SPEC.md` through the reference harness three times, at temperatures 0.2, 0.6, and 1.0, with a fixed seed per temperature that is secret until grades are released. Your hidden-test score is the best of the three. A run that exceeds {{REGEN_TIMEOUT}} minutes or produces a solution that does not start scores zero for that run.

**Written component** (`WRITTEN.md`, one page), scored 0–3 on each of:

- *Accuracy*: explain how you developed the specification; does it match what `SPEC.md` says?
- *Twist specificity*: which lines of your specification handle the twist, and why those?
- *Candor*: name one thing the harness got wrong and what you changed.
- {{GRADUATE ONLY}} *Prediction*: which hidden categories will your specification fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, the code the harness produced during your development, the number of times you regenerated, and the process note.

## 10. Integrity

Specifications are text and are treated like code: they are submitted to {{SIMILARITY_TOOL}}, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. Pairs submit one directory and both sign the ledger. The twist changes every semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

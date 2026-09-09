# {{COURSE}} Project {{N}}: {{TITLE}} (Mastery Project)

*Replace every `{{…}}`. Keep the section order.*

## 1. The task

{{One paragraph. What the program must do, referring to the published resource for the rule that differs from the textbook version.}}

## 2. The published resource and the ledger

The full task, including the twist, is at:

**{{RESOURCE_URL}}**

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your harness must sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page. A submission with no ledger entry is incomplete and will not be graded until resolved.**

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try.

## 3. Interface contract

| | |
|---|---|
| Language | {{LANGUAGE}} |
| Entry point | `{{ENTRY}}` in the root of your submission |
| Input | one JSON object on stdin |
| Output | one JSON object on stdout, nothing else |
| Time limit | {{TEST_TIMEOUT}} seconds per test case |

Worked example:

```
$ echo '{{EXAMPLE_INPUT}}' | python3 {{ENTRY}}
{{EXAMPLE_OUTPUT}}
```

## 4. Tests

Public tests are in `tests/public/`:

```
python3 tools/run_tests.py --solution . --tests tests/public
```

Hidden categories (names and counts; cases released after grading):

| Category | Cases | Weight | Graduate only |
|---|---|---|---|
| {{CATEGORY}} | {{N}} | {{W}} | {{yes/no}} |

## 5. AI use

Use any harness you like. The course provides a free reference setup, **{{HARNESS}} with `{{MODEL}}`**, install guide at {{INSTALL_URL}} and the [student primer](./student-primer.md), shared server at `{{OLLAMA_HOST}}`. Your code is graded, not your tool. You are expected to understand every line you submit; the written component asks you to explain one design decision.

## 6. What to submit

| File | Cap |
|---|---|
| your solution directory, `{{ENTRY}}` at its root | — |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded |

## 7. Milestone ({{MILESTONE_DATE}}, 10%)

Your solution passes the public suite. Submit the test runner's JSON output. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Ledger entry | gate |
| Milestone | 10 |
| Hidden tests (run once) | 70, twist categories carry 35 |
| Written component | 20 |

**Written component** (`WRITTEN.md`, one page), 0–3 on each of:

- *Accuracy*: explain one design decision; does it match the code?
- *Twist specificity*: which part of your solution handles the twist, and why that way?
- *Candor*: name one input class your solution handles badly.
- {{GRADUATE ONLY}} *Prediction*: which hidden categories will you fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, how many times you regenerated, the process note.

## 10. Integrity

Solutions are checked for similarity. Pairs submit one directory and both sign the ledger. The twist changes every semester.
{{IF VARIANTS}} Your resource URL carries a parameter unique to you; hidden tests are generated for your parameter.{{END}}

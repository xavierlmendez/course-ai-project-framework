# CS 5xx Project 2: Grid pathfinding with momentum (Mastery Project)

## 1. The task

Write a program that finds a minimum-cost path between two cells of a grid with walls, where the cost of a step depends on the direction you arrived from. The exact movement rule is stated only in the published resource; it is not the textbook unit-cost grid, and a textbook A* will not pass the twist categories.

## 2. The published resource and the ledger

The full task, including the rule that differs from the textbook version, is at:

**http://localhost:8080/** from your laptop, **http://host.docker.internal:8080/** from inside the course sandbox.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your harness must sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page. A submission with no ledger entry is incomplete and will not be graded until resolved.**

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12 |
| Entry point | `solve.py` in the root of your submission |
| Input | one JSON object on stdin: `{"grid": [...], "start": [r, c], "goal": [r, c]}` |
| Output | one JSON object on stdout, nothing else: `{"cost": int or null, "path": [[r, c], ...]}` |
| Time limit | 10 seconds per test case |

Worked example:

```
$ echo '{"grid": ["......", "......"], "start": [0, 0], "goal": [0, 5]}' | python3 solve.py
{"cost": 4, "path": [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5]]}
```

## 4. Tests

Public tests are in `tests/public/`:

```
python3 tools/run_tests.py --solution . --tests tests/public
```

Any minimum-cost path is accepted; a checker validates the path and its cost. Hidden categories (names and counts; cases released after grading):

| Category | Cases | Weight | Graduate only |
|---|---|---|---|
| basic | 6 | 1 | no |
| walls | 6 | 1 | no |
| unreachable | 4 | 1 | no |
| twist_long_run | 8 | 1.5 | no |
| twist_detour | 6 | 1.5 | no |
| grad_large | 4 | 1 | yes |

## 5. AI use

Use any harness you like. The course provides a free reference setup, **OpenCode with `qwen2.5-coder:14b`** on Ollama, install guide at the course site, shared server at `http://<course-ollama-host>:11434`. Your code is graded, not your tool. You are expected to understand every line you submit; the written component asks you to explain one design decision.

## 6. What to submit

| File | Cap |
|---|---|
| your solution directory, `solve.py` at its root | — |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded |

## 7. Milestone (end of week 1, 10%)

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
- Graduate only: *Prediction*: which hidden categories will you fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, how many times you regenerated, the process note.

## 10. Integrity

Solutions are submitted to {{SIMILARITY_TOOL}}, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. Pairs submit one directory and both sign the ledger. The twist changes every semester.

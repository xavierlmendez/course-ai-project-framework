# CS 6xxx Project 2: Job Scheduling with Cooldown (Mastery Project)

## 1. The task

Write a program that chooses a maximum-weight set of jobs from a list, where the rule for which jobs may follow one another is not the textbook rule. The exact rule, and the cooldown parameter that is specific to you, are on the published resource. Read it.

## 2. The published resource and the ledger

The full task, including the twist, is at:

**http://localhost:8080/?v=<your variant>** (from a laptop) or **http://host.docker.internal:8080/?v=<your variant>** (from inside the sandbox)

Your variant is your student ID (pairs: the first partner's ID). Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your harness must sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page. A submission with no ledger entry is incomplete and will not be graded until resolved.**

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12 |
| Entry point | `solve.py` in the root of your submission |
| Input | one JSON object on stdin, with `variant` and `jobs` |
| Output | one JSON object on stdout, `total` and `chosen`, nothing else |
| Time limit | 10 seconds per test case |

Worked example:

```
$ echo '{"variant":"demo","jobs":[{"id":"a","start":0,"end":5,"weight":10,"class":"S"},{"id":"b","start":6,"end":9,"weight":3,"class":"S"},{"id":"c","start":5,"end":8,"weight":4,"class":"P"}]}' | python3 solve.py
{"total": 14, "chosen": ["a", "c"]}
```

## 4. Tests

Public tests are in `tests/public/`. **They are generated for the variant `demo` (g = 2), not for yours.** Your hidden tests are generated for your variant.

```
python3 tools/run_tests.py --solution . --tests tests/public
```

Hidden categories (names and counts; cases released after grading):

| Category | Cases | Weight | Graduate only |
|---|---|---|---|
| basic | 5 | 1 | no |
| overlaps | 5 | 1 | no |
| twist_cooldown | 6 | 1 (twist) | no |
| twist_class | 6 | 1 (twist) | no |
| grad_large | 4 | 1 | yes |

## 5. AI use

Use any harness you like. The course provides a free reference setup, **OpenCode with `qwen2.5-coder:14b`** on Ollama, install guide at `<INSTALL_URL>`, shared server at `<OLLAMA_HOST>`. Your code is graded, not your tool. You are expected to understand every line you submit; the written component asks you to explain one design decision.

## 6. What to submit

| File | Cap |
|---|---|
| your solution directory, `solve.py` at its root | — |
| `variant.txt` containing your variant string | one line |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded |

## 7. Milestone (end of week 1, 10%)

Your solution passes the public suite. Submit the test runner's JSON output. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Ledger entry | gate |
| Milestone | 10 |
| Hidden tests (run once, generated for your variant) | 70, twist categories carry 35 |
| Written component | 20 |

**Written component** (`WRITTEN.md`, one page), 0–3 on each of:

- *Accuracy*: explain one design decision; does it match the code?
- *Twist specificity*: which part of your solution handles the twist, and why that way?
- *Candor*: name one input class your solution handles badly.
- Graduate only. *Prediction*: which hidden categories will you fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, how many times you regenerated, the process note.

## 10. Integrity

Solutions are checked for similarity. Pairs submit one directory and both sign the ledger. The twist changes every semester. Your resource URL carries a parameter unique to you; hidden tests are generated for your parameter, so a copied solution that hard-codes someone else's g fails your tests.

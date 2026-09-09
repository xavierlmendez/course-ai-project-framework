# CS 5xx Project 2: Grid pathfinding with momentum (Mastery Project)

## 1. The task

Write a program that finds a minimum-cost path between two cells of a grid with walls, where the cost of a step depends on the direction you arrived from. The exact movement rule is stated only in the published resource; it is not the textbook unit-cost grid, and a textbook A* will not pass the twist categories.

## 2. The published resource and the ledger

The full task, including the rule that differs from the textbook version, is at:

**http://localhost:8081/** from your laptop, **http://host.docker.internal:8081/** from inside the grading sandbox. (8081 is this project's `resource_port`.)

To practise at home, start that server yourself from the root of the course repository:

```
python3 tools/ledger_server.py --project examples/02-astar-type-a/project.json --allow-in-repo
```

It listens on the project's `resource_port`, prints the nonce it is serving, and writes `examples/02-astar-type-a/ledger.tsv`. `--allow-in-repo` is needed only because that path is inside a checkout: the server refuses by default so that a real ledger of student IDs is never one `git add .` from being committed, and a practice ledger is throwaway. That is your own ledger; the graded one is the course server your instructor announces.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your harness must sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page. A submission with no ledger entry is incomplete and will not be graded until resolved.**

**The ID format is three upper-case letters followed by six digits** — `ABC123456`. That is the only form the ledger accepts; anything else (a lower-case prefix, a different number of digits) is rejected with a message saying so. IDs are upper-cased before they are recorded, so `abc123456` is stored as `ABC123456`. A pair gives both, comma-separated: `ABC123456,DEF654321`.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12 or later |
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

Public tests are in `examples/02-astar-type-a/tests/public/`. From the root of the course repository:

```
python3 tools/run_tests.py --solution <your dir> \
  --tests examples/02-astar-type-a/tests/public --entry solve.py --timeout 10
```

`<your dir>` is the directory holding your submission files, for example `mywork-astar/`; use its path wherever `<your dir>` appears below. Nothing in this project writes a `runs/` directory: `runs/` belongs to the regeneration runner, which a Type A project never uses. The one file the course tools write for you is the milestone record (§7), and it lands in the directory you run the command from.

`--json` prints **only** the JSON summary; without it the tool prints both the human-readable lines and the JSON. The milestone (§7) runs this same suite for you and writes a signed record.

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

Use any harness you like. The course provides a free reference setup, **OpenCode on Ollama with the model named in `examples/02-astar-type-a/project.json`** (the `base_model` key). The install guide is the [student primer](../../templates/student-primer.md).

**If your machine cannot run the model.** With Ollama on your own machine there is nothing to edit: the `ollama_host` shipped in `project.json` is the grading container's view of the model server, and a practice run (which uses no sandbox) substitutes `127.0.0.1` for it automatically. To use the course Ollama server your instructor announces, add `"ollama_host_local"` to **your own copy** of `project.json`, set to the server URL as your machine reaches it. Leave `ollama_host` alone — it describes the grading run. Exporting `OLLAMA_HOST` does not redirect OpenCode.

Your code is graded, not your tool. You are expected to understand every line you submit; the written component asks you to explain one design decision.

## 6. What to submit

| File | Cap |
|---|---|
| your solution directory, `solve.py` at its root | — |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded |

## 7. Milestone (end of week 1, 10%)

Your solution passes the public suite. Produce the signed milestone record and submit it:

```
python3 tools/milestone.py record --project examples/02-astar-type-a/project.json \
  --solution <your dir> --student-id <your student ID>
```

It writes `milestone-astar-a.json` in the directory you ran it from — the name comes from the `name` key of that `project.json`, so a record for one project can never overwrite another's. Submit `milestone-astar-a.json`. Auto-graded pass/fail.

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

Solutions are submitted to MOSS, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. Pairs submit one directory and both sign the ledger. The twist changes every semester.

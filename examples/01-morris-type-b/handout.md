# CS Artificial Intelligence Project 2: Morris Game, Variant (Specification Project)

*Four parts, eight programs. Each part is graded separately and combined with the weights below. Keep the section order.*

## 1. The task

Write specifications from which the reference harness produces programs that play the opening and midgame of a Morris variant by MINIMAX and ALPHA-BETA search, for White and for Black, with the class's static estimation and then with an improved one of your own. The complete rules, the board, and the exact algorithms are on the published resource; this handout does not repeat them.

## 2. The published resource and the ledger

The full task, including the board that differs from the textbook nine men's morris board, is at:

**http://localhost:8080/** (from a laptop) · **http://host.docker.internal:8080/** (from inside the sandbox)

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Each specification must tell the agent to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12, standard library only, one file per program |
| Entry points | `MiniMaxOpening.py`, `MiniMaxGame.py`, `ABOpening.py`, `ABGame.py`, `MiniMaxOpeningBlack.py`, `MiniMaxGameBlack.py`, `MiniMaxOpeningImproved.py`, `MiniMaxGameImproved.py` |
| Invocation | `python3 <Program>.py <input file> <output file> <depth>` |
| Input | a file holding one 23-character board of `W`, `B`, `x` |
| Output file | the chosen board, one line |
| Stdout | exactly three lines, shown below |
| Time limit | 30 seconds per test case |
| Generation order | ascending index for children and removals, as the resource states; the count of positions evaluated depends on it |

```
$ echo xxxxxxxxxWxxxxxxBxxxxxx > in.txt
$ python3 MiniMaxOpening.py in.txt out.txt 2
Board Position: WxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

## 4. Tests

Public tests are in `part-<N>/tests/public/`. Run them with:

```
python3 tools/run_tests.py --solution <dir> --tests part-I/tests/public --entry MiniMaxOpening.py --timeout 30
```

Hidden categories (names, counts, weights and equivalence policy; cases released after grading):

| Part | Category | Cases | Weight | Policy | Graduate only |
|---|---|---|---|---|---|
| I | opening_move | 6 | 2 | estimate: same MINIMAX estimate as the reference, board a legal result | no |
| I | opening_mill | 6 | 2 | estimate; positions where the best move completes a mill | no |
| I | evaluations_count | 4 | 1 | strict: all three lines match, depth 2 | no |
| I | grad_depth4 | 4 | 1 | estimate, depth 4 | yes |
| II | ab_pruning | 4 | 2 | ab: estimate equals MINIMAX's, count strictly lower | no |
| II | grad_depth4 | 2 | 1 | ab, depth 4 | yes |
| III | black_move, black_mill, colors_back, grad_depth4 | | 2, 2, 1, 1 | estimate / estimate / strict / estimate | last only |
| IV | improved_differs, improved_valid, grad_depth4 | | 2, 2, 1 | valid: legal move, correct format; differs from baseline where your write-up says it does | last only |

"Estimate" policy means ties between equal-valued moves are not penalised; "strict" means the count is compared too, which is why the generation order is in the contract.

## 5. The reference harness

Your grade comes from **OpenCode with model `qwen2.5-coder:14b`**, run by the TAs. Develop with whatever you like; optimizing for another tool is pointless.

Install guide: `docs/install-opencode-ollama.md`. A shared Ollama server is at `ollama.cs.example.edu:11434` for anyone whose machine cannot run the model.

Run a specification the way the TAs will:

```
python3 tools/runner.py --project part-I/project.json --submission <dir> --run-tag practice
```

## 6. What to submit

One directory per part, each containing exactly:

| File | Cap |
|---|---|
| `SPEC.md`, one per part directory | 1,500 words each including supporting files |
| `PROCESS.md` | 1 page per part; required, not graded |
| `WRITTEN.md` | 1 page for the whole project, 600 words; graded |
| Part IV only: `MyStaticEstimation.md` | 1 page: your function, two positions where it chooses differently from the baseline, and why it is better |

Do **not** submit generated code. It is not graded.

## 7. Milestone (end of week 1, 10%)

Your Part I `SPEC.md` passes the public suite through the reference harness. Produce the record with `tools/milestone.py record` and submit it. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Milestone | 10 |
| Hidden tests, best of 3 regenerations per program | 70, twist categories carry 35 |
| Written component | 20 |

The 70 hidden-test points are split across parts: **Part I 45%, Part II 35%, Part III 10%, Part IV 10%** of the 70. Each part is graded on its own categories, then combined with those weights.

**Regeneration.** The TAs run each specification through the reference harness three times, at temperatures 0.2, 0.6 and 1.0, with a fixed seed per temperature that is secret until grades are released. Your hidden-test score per program is the best of the three. A run that exceeds 20 minutes or produces a program that does not start scores zero for that run.

**Written component** (`WRITTEN.md`, one page per part), 0–3 on each of:

- *Accuracy*: explain how you developed the specification.
- *Twist specificity*: which lines of your specification make the program use this board's lines rather than the textbook board's, and, for Part II, which lines make alpha-beta return minimax's exact estimate?
- *Candor*: name one thing the harness got wrong and what you changed.
- *Graduate only, Prediction*: which hidden categories will your specification fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, the code the harness produced during your development, the number of times you regenerated, the process note.

## 10. Integrity

Specifications are text and are checked for similarity like code. This is an individual project unless your section allows pairs; a pair submits one directory per part and both sign the ledger. The board and its lines change next semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

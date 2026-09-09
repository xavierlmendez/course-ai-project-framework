# CS Artificial Intelligence Project 2: Morris Game, Variant (Specification Project)

*One program per part, listed in §3. The parts that are graded and their weights are the ones in `parts.json`; each part is graded separately and combined with those weights.*

## 1. The task

Write specifications from which the reference harness produces programs that play the **opening** of a Morris variant by MINIMAX and ALPHA-BETA search, for White and then for Black, with the class's static estimation and then with an improved one of your own. The complete rules, the board, and the exact algorithms are on the published resource; this handout does not repeat them. Every part concerns the opening phase only.

## 2. The published resource and the ledger

The full task, including the board that differs from the textbook nine men's morris board, is at:

**http://localhost:8080/** (from a laptop) · **http://host.docker.internal:8080/** (from inside the grading sandbox)

To practise at home, start that server yourself from the root of the course repository:

```
python3 tools/ledger_server.py --project examples/01-morris-type-b/part-I/project.json \
  --port 8080 --allow-in-repo
```

It prints the nonce it is serving, writes `examples/01-morris-type-b/ledger.tsv`, and is your own ledger, not the course one. `--allow-in-repo` is needed only because that path is inside a checkout: the server refuses by default so a real ledger of student IDs is never one `git add .` from being committed, and a practice ledger is throwaway. The graded ledger is the course server your instructor announces.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Each specification must tell the agent to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12, standard library only, one file per program |
| Entry points | Part I `MiniMaxOpening.py`, Part II `ABOpening.py`, Part III `MiniMaxOpeningBlack.py`, Part IV `MiniMaxOpeningImproved.py` — one program per part, each the `entry` in that part's `project.json` |
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

Public tests are in each part's `tests/public/`. From the root of the course repository, for Part I:

```
python3 tools/run_tests.py --solution <your dir> \
  --tests examples/01-morris-type-b/part-I/tests/public \
  --entry MiniMaxOpening.py --timeout 30
```

For another part, swap `part-I` and the `--entry` for that part's entry point from §3.

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

Your grade comes from **OpenCode with the model named in each part's `project.json`** (the `base_model` key), run by the TAs. Develop with whatever you like; optimizing for another tool is pointless. <!-- model: from project.json -->

Install guide: the [student primer](../../templates/student-primer.md). Read it before the milestone.

If your machine cannot run the model, use the course Ollama server your instructor announces: set `ollama_host` in your own copy of the part's `project.json` to that URL. The runner writes it into the `opencode.json` it generates, verbatim, so it must be an address the machine you are running on can reach. Exporting `OLLAMA_HOST` does not redirect OpenCode.

Run a specification the way the TAs will, from the root of the course repository:

```
python3 tools/runner.py --project examples/01-morris-type-b/part-I/project.json \
  --submission <your part-I dir> --practice
```

`--practice` needs nothing you do not have: it runs outside the grading sandbox, tags the run `practice`, runs that part's **public** suite, writes `seeds.practice.json` with three seeds of your own (the grading seeds are secret until grades are out), and creates the pinned per-temperature models if your Ollama has none.

## 6. What to submit

One directory per part, each containing exactly:

| File | Cap |
|---|---|
| `SPEC.md` — exactly that name, in each part's directory. It is the file the harness is told to read (`spec` in that part's `project.json`) | 1,500 words each including supporting files |
| `PROCESS.md` | 1 page per part; required, not graded |
| `WRITTEN.md` | 1 page for the whole project, 600 words; graded |
| Part IV only: `MyStaticEstimation.txt`, named inside your Part IV `SPEC.md` so the harness receives it | 1 page: your function, two positions where it chooses differently from the baseline, and why it is better |

Do **not** submit generated code. It is not graded.

## 7. Milestone (end of week 1, 10%)

Your Part I `SPEC.md` passes the public suite through the reference harness. Do the `--practice` run in §5, then produce the signed milestone record from the directory it wrote and submit that file:

```
python3 tools/milestone.py record \
  --project examples/01-morris-type-b/part-I/project.json \
  --solution runs/<your part-I dir>/practice-k1-work \
  --regeneration runs/<your part-I dir>/practice-k1.json \
  --student-id ABC123456 --out milestone.json
```

Submit `milestone.json`. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Milestone | 10 |
| Hidden tests, best of 3 regenerations per part | 70, twist categories carry 35 |
| Written component | 20 |

The 70 hidden-test points are split across parts: **Part I 45%, Part II 35%, Part III 10%, Part IV 10%** of the 70. Each part is graded on its own categories, then combined with those weights.

**Regeneration.** The TAs run each specification through the reference harness three times, at temperatures 0.2, 0.6 and 1.0, with a fixed seed per temperature that is secret until grades are released. Your hidden-test score per part is the best of the three. A run that exceeds 20 minutes or produces a program that does not start scores zero for that run.

**Written component** (`WRITTEN.md`, one page per part), 0–3 on each of:

- *Accuracy*: explain how you developed the specification.
- *Twist specificity*: which lines of your specification make the program use this board's lines rather than the textbook board's, and, for Part II, which lines make alpha-beta return minimax's exact estimate?
- *Candor*: name one thing the harness got wrong and what you changed.
- *Graduate only, Prediction*: which hidden categories will your specification fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, the code the harness produced during your development, the number of times you regenerated, the process note.

## 10. Integrity

Specifications are text and are treated like code: they are submitted to MOSS, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. This is an individual project unless your section allows pairs; a pair submits one directory per part and both sign the ledger. The board and its lines change next semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

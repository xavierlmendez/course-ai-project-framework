# CS Artificial Intelligence Project 2: Morris Game, Variant (Specification Project)

*Four parts, eight programs — an Opening and a Game program in each part, one directory per program. The programs that are graded and their weights are the ones in `parts.json`; each program is graded separately and combined with those weights.*

## 1. The task

Write specifications from which the reference harness produces programs that play the opening and the midgame/endgame of a Morris variant by MINIMAX and ALPHA-BETA search, for White and for Black, with the class's static estimation and then with the improved one. The complete rules, the board, the hopping rule, both static estimations and the improved estimation are on the published resource; this handout does not repeat them.

## 2. The published resource and the ledger

The full task, including the board that differs from the textbook nine men's morris board, is at:

**http://localhost:8080/** (from a laptop) · **http://host.docker.internal:8080/** (from inside the grading sandbox)

To practise at home, start that server yourself from the root of the course repository:

```
python3 tools/ledger_server.py --project examples/01-morris-type-b/part-I-opening/project.json \
  --port 8080 --allow-in-repo
```

It prints the nonce it is serving, writes `examples/01-morris-type-b/ledger.tsv`, and is your own ledger, not the course one. `--allow-in-repo` is needed only because that path is inside a checkout: the server refuses by default so a real ledger of student IDs is never one `git add .` from being committed, and a practice ledger is throwaway. The graded ledger is the course server your instructor announces.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Each specification must tell the harness to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

**The ID format is three upper-case letters followed by six digits** — `ABC123456`. That is the only form the ledger accepts; anything else (a lower-case prefix, a different number of digits) is rejected with a message saying so. IDs are upper-cased before they are recorded, so `abc123456` is stored as `ABC123456`. A pair gives both, comma-separated: `ABC123456,DEF654321`. Write the ID into every specification in that form.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12 or later, standard library only, one file per program |
| Entry points | `MiniMaxOpening.py`, `MiniMaxGame.py`, `ABOpening.py`, `ABGame.py`, `MiniMaxOpeningBlack.py`, `MiniMaxGameBlack.py`, `MiniMaxOpeningImproved.py`, `MiniMaxGameImproved.py` — one program per directory, each the `entry` in that directory's `project.json` |
| Invocation | `python3 <Program>.py <input file> <output file> <depth>` |
| Input | a file holding one 23-character board of `W`, `B`, `x` |
| Output file | the chosen board, one line |
| Stdout | exactly three lines, shown below |
| Time limit | 30 seconds per test case |
| Generation order | ascending index for children and removals, neighbours in the order the adjacency table lists them, as the resource states; the count of positions evaluated depends on it |

```
$ echo xxxxxxxxxWxxxxxxBxxxxxx > in.txt
$ python3 MiniMaxOpening.py in.txt out.txt 2
Board Position: WxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

## 4. Tests

Each program has its own directory, `part-<N>-opening/` or `part-<N>-game/`, and its own public suite in `tests/public/`. From the root of the course repository, for the Part I Opening program:

```
python3 tools/run_tests.py --solution <your part-I-opening dir> \
  --tests examples/01-morris-type-b/part-I-opening/tests/public \
  --entry MiniMaxOpening.py --timeout 30 \
  --project examples/01-morris-type-b/part-I-opening/project.json
```

For another program, swap `part-I-opening` for that program's directory and the `--entry` and `--project` for that program's entry point and `project.json`. `--project` makes your run apply the same equivalence policy per category that grading applies — `estimate`, `ab`, `strict` — instead of comparing every output exactly.

**Two names used throughout this handout.** `<your part-I-opening dir>` — and `<your dir>` generally — is the directory holding your submission files for that program, for example `mywork/part-I-opening/`. `runs/` is where the runner writes: it creates `runs/<dir name>/` beside where you run the command, where `<dir name>` is the **last segment** of `<your dir>` — if your directory is `mywork/part-I-opening`, the runner writes `runs/part-I-opening/` — and every record and working directory named below lives inside it.

`--json` prints **only** the JSON summary; without it the tool prints both the human-readable lines and the JSON.

Hidden categories (names, counts, weights and equivalence policy; cases released after grading). The **twist** categories are marked `*`; in every program they carry exactly half the non-graduate weight.

| Program | Category | Cases | Weight | Policy | Graduate only |
|---|---|---|---|---|---|
| MiniMaxOpening | opening_move | 6 | 2 | estimate | no |
| MiniMaxOpening | opening_mill `*` | 6 | 3 | estimate; the best move completes a diagonal-spoke mill | no |
| MiniMaxOpening | evaluations_count | 4 | 1 | strict: all three lines match, depth 2 | no |
| MiniMaxOpening | grad_depth4 | 4 | 1 | estimate, depth 4 | yes |
| MiniMaxGame | game_move | 5 | 2 | estimate | no |
| MiniMaxGame | game_hopping | 4 | 1 | estimate; the mover holds exactly three pieces | no |
| MiniMaxGame | game_mill `*` | 6 | 3 | estimate; a diagonal-spoke mill and its capture decide the move | no |
| MiniMaxGame | grad_depth3 | 4 | 1 | estimate, depth 3 | yes |
| ABOpening | ab_pruning | 5 | 3 | ab: estimate equals MINIMAX's, count strictly lower | no |
| ABOpening | ab_diagonal_mill `*` | 6 | 3 | ab, on positions where a diagonal-spoke mill decides the move | no |
| ABOpening | grad_depth4 | 4 | 1 | ab, depth 4 | yes |
| ABGame | ab_game_pruning | 5 | 3 | ab | no |
| ABGame | ab_game_mill `*` | 6 | 3 | ab, on positions where a diagonal-spoke mill decides the move | no |
| ABGame | grad_depth3 | 4 | 1 | ab, depth 3 | yes |
| MiniMaxOpeningBlack | black_move | 4 | 2 | estimate, Black to move | no |
| MiniMaxOpeningBlack | colors_back | 3 | 1 | strict: all three lines, so a colour-swapped board fails | no |
| MiniMaxOpeningBlack | black_mill `*` | 6 | 3 | estimate; Black closes a diagonal-spoke mill | no |
| MiniMaxOpeningBlack | grad_depth4 | 4 | 1 | estimate, depth 4 | yes |
| MiniMaxGameBlack | black_game_move | 5 | 2 | estimate, Black to move | no |
| MiniMaxGameBlack | black_hopping | 4 | 1 | estimate; Black holds exactly three pieces | no |
| MiniMaxGameBlack | black_game_mill `*` | 6 | 3 | estimate; a diagonal-spoke mill decides Black's move | no |
| MiniMaxGameBlack | grad_depth3 | 4 | 1 | estimate, depth 3 | yes |
| MiniMaxOpeningImproved | improved_valid | 5 | 3 | valid: legal move and correct format only | no |
| MiniMaxOpeningImproved | improved_better `*` | 6 | 3 | estimate against the **improved** reference, on positions the baseline estimator misjudges | no |
| MiniMaxOpeningImproved | grad_depth3 | 4 | 1 | valid, depth 3 | yes |
| MiniMaxGameImproved | improved_game_valid | 5 | 3 | valid | no |
| MiniMaxGameImproved | improved_game_better `*` | 6 | 3 | estimate against the improved reference | no |
| MiniMaxGameImproved | grad_depth3 | 4 | 1 | valid, depth 3 | yes |

"Estimate" policy means ties between equal-valued moves are not penalised; "strict" means the count is compared too, which is why the generation order is in the contract; "valid" checks only that the move is legal and the three lines are well formed.

**Part IV is graded against positions where the baseline estimator is weak.** The `improved_*_better` cases are positions where the mill and threat terms change which move wins. A specification that produces the handout's baseline estimator will pass `improved_valid` — the moves are legal — and score zero on the twist category. Copying the baseline is the failure this part exists to catch.

## 5. The reference harness

Your grade comes from **OpenCode with the model named in each program's `project.json`** (the `base_model` key), run by the TAs. Develop with whatever you like; optimizing for another tool is pointless.

Install guide: the [student primer](../../templates/student-primer.md). Read it before the milestone.

**If your machine cannot run the model.** Running Ollama locally needs no edit at all: the `ollama_host` shipped in each `project.json` is the grading container's view of the model server, and a practice run (which uses no sandbox) substitutes `127.0.0.1` for it automatically. To use the course Ollama server your instructor announces, add `"ollama_host_local"` to **your own copy** of that program's `project.json`, set to the server URL as your machine reaches it. Leave `ollama_host` alone — it describes the grading run. Exporting `OLLAMA_HOST` does not redirect OpenCode.

Run a specification the way the TAs will, from the root of the course repository:

```
python3 tools/runner.py --project examples/01-morris-type-b/part-I-opening/project.json \
  --submission <your part-I-opening dir> --practice
```

`--practice` needs nothing you do not have: it runs outside the grading sandbox, tags the run `practice`, runs that program's **public** suite, writes `seeds.practice.json` with three seeds of your own (the grading seeds are secret until grades are out), and creates the pinned per-temperature models if your Ollama has none.

## 6. What to submit

One top-level submission directory. Inside it, one directory per **program** — eight of them, named as the program directories are (`part-I-opening`, `part-I-game`, `part-II-opening`, … `part-IV-game`) — and, at the top level beside them, **one `WRITTEN.md` and one `PROCESS.md` for the whole project, 600 words each**. There is not one of those per program: the written component and the process note are course-level, written once and scored once (§8), and the pre-scan looks for them in the top-level directory.

```
<your dir>/
  part-I-opening/SPEC.md          … one SPEC.md per program, eight in all
  part-I-game/SPEC.md
  …
  part-IV-game/SPEC.md
  WRITTEN.md                      one page for the whole project
  PROCESS.md                      one page for the whole project
```

| File | Where | Cap |
|---|---|---|
| `SPEC.md` — exactly that name | in each program's directory; it is the file the harness is told to read (`spec` in that program's `project.json`) | 1,500 words each including supporting files |
| `PROCESS.md` | top level, one for the project | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | top level, one for the project | 1 page, 600 words; graded |
| Part IV only: `MyStaticEstimation.md`, named inside your Part IV `SPEC.md` so the harness receives it | in `part-IV-opening/` and `part-IV-game/` as your specification requires | 1 page: the improved function as you specified it, two positions where it chooses differently from the baseline, and why its choice is better |

Do **not** submit generated code. It is not graded.

## 7. Milestone (end of week 1, 10%)

Your `part-I-opening/SPEC.md` passes the public suite through the reference harness. Do the `--practice` run in §5 first — a real run, not a dry run — then build the record from what it wrote:

```
python3 tools/milestone.py record \
  --project examples/01-morris-type-b/part-I-opening/project.json \
  --solution runs/<dir name>/practice-k1-work \
  --regeneration runs/<dir name>/practice-k1.json \
  --student-id <your student ID>
```

`<dir name>` is the last segment of your Part I Opening directory, as §4 says: with `mywork/part-I-opening` the runner wrote `runs/part-I-opening/`, so those two paths are `runs/part-I-opening/practice-k1-work` and `runs/part-I-opening/practice-k1.json`.

This is a Type B project, so `--regeneration` is **required** and `--solution` must be that regeneration's own working directory — the `-work` directory beside the record. A record built from anything else, including a dry-run record (named `*.dry.json`), is rejected.

It writes `milestone-morris-p1-open-I-opening.json` in the directory you ran it from — the name comes from the `name` and `part` keys of that program's `project.json`, so the records for eight programs cannot overwrite one another. Submit `milestone-morris-p1-open-I-opening.json`. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Milestone | 10 |
| Hidden tests, best of 3 regenerations per program | 70, of which twist categories carry 35 |
| Written component | 20 |

The 70 hidden-test points are split across the eight programs. The part weights are **Part I 45%, Part II 35%, Part III 10%, Part IV 10%** of the 70, and each part splits its weight evenly between its Opening and its Game program:

| Program | Share of the 70 |
|---|---|
| MiniMaxOpening, MiniMaxGame | 22.5% each |
| ABOpening, ABGame | 17.5% each |
| MiniMaxOpeningBlack, MiniMaxGameBlack | 5% each |
| MiniMaxOpeningImproved, MiniMaxGameImproved | 5% each |

Each program is graded on its own categories, then combined with those weights. Because every program's twist categories carry exactly half its non-graduate weight, the twist categories carry half of the 70 — that is, 35 points — across the project as a whole. The milestone and the written component are course-level and are counted once, not once per program.

**Regeneration.** The TAs run each specification through the reference harness three times, at temperatures 0.2, 0.6 and 1.0, with a fixed seed per temperature that is secret until grades are released. Your hidden-test score per program is the best of the three. A run that exceeds 20 minutes or produces a program that does not start scores zero for that run.

**Written component** (`WRITTEN.md`, one page for the whole project, at the top level of your submission — not one per program), 0–3 on each of:

- *Accuracy*: explain how you developed the specification.
- *Twist specificity*: which lines of your specification make the program use this board's lines rather than the textbook board's, and, for Part II, which lines make alpha-beta return minimax's exact estimate?
- *Candor*: name one thing the harness got wrong and what you changed.
- *Graduate only, Prediction*: which hidden categories will your specification fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, the code the harness produced during your development, the number of times you regenerated, the process note.

## 10. Integrity

Specifications are text and are treated like code: they are submitted to MOSS, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. This is an individual project unless your section allows pairs; a pair submits one submission directory and both sign the ledger. The board and its lines change next semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

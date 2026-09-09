# Example 01: Morris Game, Variant (the professor's Spring 2026 Project 2, recast)

**Type B, multi-part, argv-files interface contract, per-category equivalence policies.** This is the professor's actual previous project (`docs/research/prior-project-spring-2026.md`) rewritten into the framework so he can compare line by line. Reference programs are Xavier Mendez's own implementations from his submission, used with his permission; test boards are his too.

## What this example showcases

1. **The real project as a Type B multi-part project.** Four parts (MINIMAX 45%, ALPHA-BETA 35%, Black 10%, improved estimation 10%), eight programs, each a separate specification. Parts I and II are fully built here (one program each: `MiniMaxOpening`, `ABOpening`); Parts III and IV are `project.json` stubs with their categories and policies so the shape is visible.
2. **The argv-files contract.** The professor's CLI, `python3 <Prog>.py <input> <output> <depth>`, with the exact three-line stdout, is expressed as `NNN.args` / `NNN.in.txt` / `NNN.stdout.txt` / `NNN.outfile.txt` cases; `tools/run_tests.py` runs them unchanged.
3. **Equivalence policies instead of "functionally identical".** Every category names its policy in `project.json`: `estimate` (same MINIMAX estimate, board a legal result, ties free), `strict` (all three lines), `ab` (estimate equals minimax's, count strictly lower), `valid` (Part IV, legal move and format only). The policies live in each category's `check.py`.
4. **Parts combined by `tools/combine_parts.py`** with `parts.json` weights.
5. **The order-dependence lesson.** The positions-evaluated count depends on child-generation order, which the original handout let vary. Here the contract fixes it (ascending index for children and removals, first equal child wins), the `evaluations_count` category is the only place the count is compared, and it carries weight 1 of 6. Estimate categories ignore the count.

## Interface

```
python3 MiniMaxOpening.py in.txt out.txt 2
Board Position: WxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

## Categories

| Part | Category | Weight | Policy | Twist | Grad |
|---|---|---|---|---|---|
| I | opening_move | 2 | estimate | | |
| I | opening_mill | 2 | estimate | yes | |
| I | evaluations_count | 1 | strict | | |
| I | grad_depth4 | 1 | estimate | | yes |
| II | ab_pruning | 2 | ab | yes | |
| II | grad_depth4 | 1 | ab | | yes |

Twist categories carry half the non-grad weight in each part. The "twist" relative to textbook nine men's morris is the 23-point board with four diagonal spokes; `opening_mill` cases are positions where the best move completes a diagonal mill.

## Verification (2026-09-08, host Python, no sandbox)

`python3 ../../tools/run_tests.py --solution part-I/reference/solution --tests part-I/tests/hidden --entry MiniMaxOpening.py --timeout 30`

| Solution | opening_move | opening_mill | evaluations_count | grad_depth4 |
|---|---|---|---|---|
| Part I reference | 6/6 | 6/6 | 4/4 | 4/4 |
| Part I canonical (standard 24-point lines, no diagonals) | 4/6 | 1/6 | 1/4 | 3/4 |

| Solution | ab_pruning | grad_depth4 |
|---|---|---|
| Part II reference | 4/4 | 2/2 |
| Part II canonical (minimax submitted as ABOpening, no pruning) | 0/4 | 0/2 |

Public suites: Part I reference 2/2, 1/1, 1/1; Part II reference 2/2. Slowest reference case: depth 4, about 0.4 s.

`make_tests.py` prints, per case, whether the canonical solution agrees; the twist cases were chosen where it does not. Xavier's reference programs already generate children and removals in ascending index order and keep the first equal-valued child, so no adjustment was needed to match the fixed order in the contract.

Dry run, `python3 ../../tools/runner.py --project part-I/project.json --submissions part-I/submissions --dry-run`:

```
1 submissions, type B, sandbox=on, out=/tmp/morris-dry
  ABC123456 k1: temperature=0.2 tag=grading-k1
  $ docker run --rm -i -v .../k1-work:/work ... -e RUN_TAG=grading-k1 -e SLOT_MODEL=ref-morris-p1-slot1 -e PROMPT=Read SPEC.md ... MiniMaxOpening.py ... harness-sandbox regenerate
  $ docker run --rm -i ... --network none ... python3 /tools/run_tests.py --solution /work --tests /tests --entry MiniMaxOpening.py --timeout 30 --json
  ABC123456 k2: ...
```

Pre-scan: `OK ABC123456 words=324` (Part I), `OK ABC123456 words=352` (Part II).

Combine simulation with four hand-written per-part gradebooks (`tools/combine_parts.py --parts parts.json gb1.csv gb2.csv gb3.csv gb4.csv`):

```
student_id,I_total,II_total,III_total,IV_total,I_status,II_status,III_status,IV_status,combined,status
ABC123456,85.0,98.33,95.0,75.83,graded,graded,graded,graded,89.75,graded
DEF654321,100.0,58.33,100.0,,graded,graded,graded,incomplete,,incomplete
```

**Not verified:** any OpenCode regeneration (not installed on the build machine). `reference/SPEC.md` for each part folds in the ten failure patterns from Xavier's `PROMPT_TUNING.md` as non-negotiables, but its pass rate on `qwen2.5-coder:14b` is unknown until the calibration checklist is run.

## Running it

```
cd examples/01-morris-type-b
python3 part-I/tests/make_tests.py            # regenerate cases from the reference (optional)
python3 ../../tools/run_tests.py --solution part-I/reference/solution --tests part-I/tests/public --entry MiniMaxOpening.py --timeout 30
python3 ../../tools/ledger_server.py --resource resource --ledger ledger.tsv --nonce <NONCE> --port 8080 --base-url http://host.docker.internal:8080
python3 ../../tools/runner.py --project part-I/project.json --create-slots
python3 ../../tools/runner.py --project part-I/project.json --submissions part-I/submissions --out part-I/runs
python3 ../../tools/grade.py --project part-I/project.json --runs part-I/runs > gb-I.csv
# ... same for each part, then:
python3 ../../tools/combine_parts.py --parts parts.json gb-I.csv gb-II.csv gb-III.csv gb-IV.csv > gradebook.csv
```

## Note to the professor: rotate the twist

This example ships the 23-point board exactly as assigned, for continuity. That board is now known to every past student and is in their prompt files, so it no longer satisfies the twist checklist's "not online in any form." Before reusing: change one line (drop a diagonal spoke and add a different one, or move the `(15,18,21)` column), or change the hopping threshold, regenerate the hidden tests with `make_tests.py`, confirm the canonical solution fails the twist categories, and re-run the calibration checklist. Also consider dropping `evaluations_count` entirely if the fixed generation order proves hard for small models to follow.

## Layout

```
parts.json                       weights 45/35/10/10
resource/index.md                published resource (rules, tables, contract, nonce, ledger)
handout.md                       filled Type B handout for the whole project
part-I/  project.json, reference/{SPEC.md, solution/MiniMaxOpening.py}, canonical/, tests/{check.py, make_tests.py, public/, hidden/}, submissions/ABC123456/
part-II/ project.json, reference/{SPEC.md, solution/ABOpening.py}, canonical/, tests/..., submissions/ABC123456/
part-III/, part-IV/              project.json stubs + README line
```

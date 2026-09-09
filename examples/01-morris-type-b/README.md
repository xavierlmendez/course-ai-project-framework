# Example 01: Morris Game, Variant (the professor's Spring 2026 Project 2, recast)

**Type B, multi-part, argv-files interface contract, per-category equivalence policies.** This is the professor's actual previous project (`docs/research/prior-project-spring-2026.md`) rewritten into the framework so he can compare line by line. Reference programs are Xavier Mendez's own implementations from his submission, used with his permission; test boards are his too.

## What this example showcases

1. **The real project, all eight programs.** Four parts (MINIMAX 45%, ALPHA-BETA 35%, Black 10%, improved estimation 10%), an Opening and a Game program in each, every one a separate specification with its own hidden suite, reference solution and canonical solution. A part directory holds one `entry`, so the unit here is the **program**: `part-I-opening/`, `part-I-game/`, `part-II-opening/`, `part-II-game/`, `part-III-opening/`, `part-III-game/`, `part-IV-opening/`, `part-IV-game/`.
2. **The argv-files contract.** The professor's CLI, `python3 <Prog>.py <input> <output> <depth>`, with the exact three-line stdout, is expressed as `NNN.args` / `NNN.in.txt` / `NNN.stdout.txt` / `NNN.outfile.txt` cases; `tools/run_tests.py` runs them unchanged.
3. **Equivalence policies instead of "functionally identical".** Every category names its policy in `project.json`: `estimate` (same MINIMAX estimate, board a legal result, ties free), `strict` (all three lines), `ab` (estimate equals minimax's, count strictly lower), `valid` (legal move and format only). The policies live in each category's `check.py`.
4. **Programs combined by `tools/combine_parts.py`** with `parts.json` weights: 22.5 / 22.5 / 17.5 / 17.5 / 5 / 5 / 5 / 5, which is the professor's 45 / 35 / 10 / 10 split evenly between each part's two programs.
5. **The order-dependence lesson.** The positions-evaluated count depends on child-generation order, which the original handout let vary. Here the contract fixes it (ascending index for children and removals, neighbours in table order, first equal child wins), and only the `evaluations_count`, `colors_back` and `ab*` categories look at the count at all.
6. **Part IV graded on the baseline's blind spot** (decision 18). The improved estimator's mill and threat terms are published on the resource; the twist category is positions where those terms change which move wins. A specification that reproduces the baseline estimator passes `improved_valid` and scores zero on `improved_better`.

## Interface

```
python3 MiniMaxOpening.py in.txt out.txt 2
Board Position: WxxxxxxxxWxxxxxxBxxxxxx
Positions evaluated by static estimation: 420.
MINIMAX estimate: 0.
```

## Categories

Twist categories are marked `*` and carry exactly half the non-graduate weight in **every** program, so they carry half of the 70 hidden-test points across the project.

| Program | Categories (weight) | Twist |
|---|---|---|
| MiniMaxOpening | opening_move 2, opening_mill\* 3, evaluations_count 1, grad_depth4 1 | opening_mill |
| MiniMaxGame | game_move 2, game_hopping 1, game_mill\* 3, grad_depth3 1 | game_mill |
| ABOpening | ab_pruning 3, ab_diagonal_mill\* 3, grad_depth4 1 | ab_diagonal_mill |
| ABGame | ab_game_pruning 3, ab_game_mill\* 3, grad_depth3 1 | ab_game_mill |
| MiniMaxOpeningBlack | black_move 2, colors_back 1, black_mill\* 3, grad_depth4 1 | black_mill |
| MiniMaxGameBlack | black_game_move 2, black_hopping 1, black_game_mill\* 3, grad_depth3 1 | black_game_mill |
| MiniMaxOpeningImproved | improved_valid 3, improved_better\* 3, grad_depth3 1 | improved_better |
| MiniMaxGameImproved | improved_game_valid 3, improved_game_better\* 3, grad_depth3 1 | improved_game_better |

The "twist" relative to textbook nine men's morris is the 23-point board with four diagonal spokes, plus the hopping rule at **exactly** three pieces. Every twist category is positions where a diagonal-spoke mill (and the capture it earns) decides the move — for Parts II and III under pruning and under the colour swap respectively — except Part IV's, which is positions where the baseline static estimation misjudges a mill threat.

## Verification (2026-09-08, host Python 3, no sandbox)

`python3 ../../tools/run_tests.py --solution <dir>/reference/solution --tests <dir>/tests/hidden --entry <Prog>.py --timeout 30`

Every reference passes every hidden case, and every canonical solution scores under 50% on the twist category. The canonicals are: for Parts I, II and III the same program on the **standard 24-point lines and adjacency** (Part II's is a fair alpha-beta, not minimax-without-pruning); for Part IV the same program with the handout's **baseline** static estimation on the correct board.

| Program | Reference (hidden) | Canonical (hidden) | Twist category, canonical |
|---|---|---|---|
| MiniMaxOpening | 6/6, 6/6, 4/4, 4/4 | 4/6, 1/6, 1/4, 3/4 | opening_mill 1/6 |
| MiniMaxGame | 5/5, 4/4, 6/6, 4/4 | 5/5, 4/4, 0/6, 4/4 | game_mill 0/6 |
| ABOpening | 5/5, 6/6, 4/4 | 5/5, 0/6, 3/4 | ab_diagonal_mill 0/6 |
| ABGame | 5/5, 6/6, 4/4 | 5/5, 0/6, 4/4 | ab_game_mill 0/6 |
| MiniMaxOpeningBlack | 4/4, 3/3, 6/6, 4/4 | 4/4, 2/3, 0/6, 4/4 | black_mill 0/6 |
| MiniMaxGameBlack | 5/5, 4/4, 6/6, 4/4 | 5/5, 4/4, 0/6, 4/4 | black_game_mill 0/6 |
| MiniMaxOpeningImproved | 5/5, 6/6, 4/4 | 5/5, 0/6, 4/4 | improved_better 0/6 |
| MiniMaxGameImproved | 5/5, 6/6, 4/4 | 5/5, 0/6, 4/4 | improved_game_better 0/6 |

Columns are in the order the category table above lists them. Public suites: every reference is 3/3 (two plain cases and one twist case, which hints at the twist without exhausting it). Slowest single case across all sixteen runs: 0.35 s, `MiniMaxOpening` at depth 4.

The eight reference programs were also checked against the professor's own recorded outputs in
`AISpring26/tests/spec.yaml` — board, evaluation count and estimate — and reproduce all of them
exactly, including `MiniMaxGame` depth 3 (4832 evaluations, −51), `ABGame` depth 3 (744), and
`MiniMaxOpeningBlack` depth 3 (8094).

Each `tests/make_tests.py` prints, per case, whether the canonical solution agrees; the twist cases were chosen where it does not. Xavier's reference programs already generate children and removals in ascending index order and keep the first equal-valued child, so no adjustment was needed to match the fixed order in the contract.

Cohort simulation, three fabricated students (a perfect undergraduate, a perfect graduate, and one whose Part IV specifications reproduce the baseline estimator), each with three run records per program, graded per program with `tools/grade.py --status status.csv` and combined with `tools/combine_parts.py --parts parts.json --written written.csv --milestone milestone.csv`:

```
student_id,...,IV-opening_hidden,IV-game_hidden,...,hidden_score,milestone,written_score,total,status
AAA111111,...,70.0,70.0,...,70.0,10.0,20.0,100.0,graded
BBB222222,...,70.0,70.0,...,70.0,10.0,20.0,100.0,graded
CCC333333,...,35.0,35.0,...,66.5,10.0,20.0,96.5,graded
```

Both perfect students total exactly 100.0, on their own denominators — the graduate's includes the `grad_*` categories and the fourth written dimension. The baseline-copying student scores 35 of 70 on each Part IV program, which is exactly the twist half, and loses 3.5 of the 70 hidden points: 5% + 5% of the 70, halved. The fabricated run records are written under `/tmp` and are not committed.

**Not verified:** any OpenCode regeneration (not installed on the build machine). `reference/SPEC.md` for each program folds in the ten failure patterns from Xavier's `PROMPT_TUNING.md` as non-negotiables, but its pass rate on `qwen2.5-coder:14b` is unknown until the calibration checklist is run.

## Running it

```
cd examples/01-morris-type-b
cd part-I-game && python3 tests/make_tests.py && cd ..     # regenerate cases from the reference (optional)
python3 ../../tools/run_tests.py --solution part-I-game/reference/solution --tests part-I-game/tests/public --entry MiniMaxGame.py --timeout 30
python3 ../../tools/ledger_server.py --resource resource --ledger ledger.tsv --nonce <NONCE> --port 8080 --base-url http://host.docker.internal:8080
python3 ../../tools/runner.py --project part-I-opening/project.json --create-slots
python3 ../../tools/runner.py --project part-I-opening/project.json --submissions part-I-opening/submissions --out part-I-opening/runs
python3 ../../tools/grade.py --project part-I-opening/project.json --runs part-I-opening/runs > gb-I-opening.csv
# ... same for each of the eight programs, in the order parts.json lists them, then:
python3 ../../tools/combine_parts.py --parts parts.json --written written.csv --milestone milestone.csv \
    gb-I-opening.csv gb-I-game.csv gb-II-opening.csv gb-II-game.csv \
    gb-III-opening.csv gb-III-game.csv gb-IV-opening.csv gb-IV-game.csv > gradebook.csv
```

## Note to the professor: rotate the twist

This example ships the 23-point board exactly as assigned, for continuity. That board is now known to every past student and is in their prompt files, so it no longer satisfies the twist checklist's "not online in any form." Before reusing: change one line (drop a diagonal spoke and add a different one, or move the `(15,18,21)` column), or change the hopping threshold from three to four, regenerate the hidden tests with each `make_tests.py`, confirm the canonical solutions still fail the twist categories, and re-run the calibration checklist. Also consider dropping `evaluations_count` entirely if the fixed generation order proves hard for small models to follow.

## Layout

```
parts.json                       eight program weights, 22.5/22.5/17.5/17.5/5/5/5/5
resource/index.md                published resource (rules for all three phases, tables, the improved
                                 estimator, the colour-swap rule, contract, nonce, ledger)
handout.md                       filled Type B handout for the whole project
part-<N>-<opening|game>/         one directory per program, eight of them, each holding
    project.json                 entry, part, categories with weights and policies
    reference/SPEC.md            the reference specification (< 1,500 words)
    reference/solution/<Prog>.py the reference program
    canonical/<Prog>.py          the twist-ignoring program the twist categories must fail
    tests/check.py               the equivalence policy for this program
    tests/check_valid.py         (Part IV only) the `valid` policy
    tests/make_tests.py          regenerates public/ and hidden/ from the reference
    tests/{public,hidden}/       the cases, one subdirectory per category
    submissions/ABC123456/       sample SPEC.md, PROCESS.md, WRITTEN.md
    seeds.secret.json            gitignored
```

# Example 02: A* with a momentum twist (Type A, published resource)

**What this example showcases.** The Mastery Project path: the student's own code is graded once, deterministically, against hidden tests; the ledger is a gate; there is no regeneration policy to explain. It also shows a twist that requires course content (state augmentation and heuristic admissibility) to get right, and a checker for problems with more than one correct answer.

## Task and I/O

Input: `{"grid": [".#..", ...], "start": [r, c], "goal": [r, c]}`. Output: `{"cost": n, "path": [[r, c], ...]}` or `{"cost": null, "path": []}`. Four-neighbour moves. Full statement in `resource/index.md`.

## The twist

Within a run of consecutive steps in the same direction, every 4th step is free (a run of length L costs `L - L//4`). Consequences: the cost depends on how you arrived (the state must carry direction and run length); a longer path with long straights can beat the shortest path; plain Manhattan distance is **inadmissible** (some steps cost 0), the tight admissible bound is `d - d//4`.

Checked against `templates/twist-checklist.md`: not a published rule anywhere we could find; fits in a page with a worked example; breaks canonical A* on two identifiable input classes (long straight runs; detours); requires admissibility reasoning; testable through the contract; hinted by one public case; different from the nine men's morris twist.

## Why the heuristic matters

`submissions/DEF654321` is a plausible student who augmented the state correctly but kept Manhattan as the heuristic. It passes every non-twist category and `twist_long_run`, and fails 4 of 6 `twist_detour` cases and all of `grad_large`, because an inadmissible heuristic returns suboptimal paths exactly when the cheap path is the longer one. That is the course-content lesson showing up in the grade without any TA reading the code.

## Categories and weights

| Category | Cases | Weight | Twist | Grad only |
|---|---|---|---|---|
| basic | 6 | 1 | | |
| walls | 6 | 1 | | |
| unreachable | 4 | 1 | | |
| twist_long_run | 8 | 1.5 | yes | |
| twist_detour | 6 | 1.5 | yes | |
| grad_large | 4 | 1 | | yes (150×150 grids, 10 s limit) |

Twist weight 3 of 6 non-grad weight, as the framework requires. `basic` and `walls` use grids of at most 4×4 so no run of 4 is possible and a canonical solver is exact there; that is what makes the canonical failure signature land only on the twist categories.

Every category directory carries `check.py` (path legality, momentum cost equals the optimum, reported cost equals path cost), because optimal paths are not unique.

## Files

```
project.json                 categories, weights, timeouts
resource/index.md            published resource ({{NONCE}}, {{BASE_URL}} substituted by the ledger server)
handout.md                   templates/handout-type-a.md filled in
reference/solution/solve.py  correct A* over (row, col, dir, run mod 4), h = d - d//4
canonical/solve.py           textbook A*, twist ignored
tests/gen.py                 generates public/ and hidden/ from the reference solution (seeded)
tests/check.py               checker copied into every category directory
tests/public/, tests/hidden/
submissions/DEF654321/       sample student: correct state, inadmissible heuristic
```

## How to run

```
cd examples/02-astar-type-a
python3 tests/gen.py                                              # regenerate tests (deterministic seed)
python3 ../../tools/run_tests.py --solution reference/solution --tests tests/hidden
python3 ../../tools/run_tests.py --solution canonical --tests tests/hidden
python3 ../../tools/runner.py --project project.json --submissions submissions --type A --out runs/   # sandboxed
python3 ../../tools/grade.py --project project.json --runs runs/ --status status.csv --written written.csv --milestone milestone.csv
```

## Verified results (2026-09-08, host Python 3.14, `--no-sandbox`)

Reference solution, hidden suite: basic 6/6, walls 6/6, unreachable 4/4, twist_long_run 8/8, twist_detour 6/6, grad_large 4/4 (slowest case 0.19 s). Public suite: 5/5.

Canonical solution, hidden suite: basic 6/6, walls 6/6, unreachable 4/4, **twist_long_run 0/8, twist_detour 0/6, grad_large 0/4**. The failure signature the calibration checklist asks for.

Sample student DEF654321, hidden suite: basic 6/6, walls 6/6, unreachable 4/4, twist_long_run 8/8, twist_detour 2/6, grad_large 0/4.

Gradebook line (undergraduate row; milestone 1; written accuracy 2, twist 3, candor 3):

```
student_id,status,grad,best_slot,hidden_score,basic_pass,walls_pass,unreachable_pass,twist_long_run_pass,twist_detour_pass,grad_large_pass,milestone,written_raw,written_score,total,note
DEF654321,graded,0,A,58.33,6/6,6/6,4/4,8/8,2/6,,10.0,8.0,17.78,86.11,
```

Same submission graded as a graduate row (no written scores entered): hidden 50.0 because `grad_large` 0/4 joins the denominator.

Not verified here: the Docker sandbox path and the ledger POST from inside a harness (no OpenCode on this machine). Both are exercised by the calibration checklist.

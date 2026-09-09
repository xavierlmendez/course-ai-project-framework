# Example 04: Job scheduling with cooldown (Type A, per-student variants)

**What this showcases.** The integrity option from `framework.md` §12: every student gets a
**variant parameter** (their student ID) in the resource URL, the published resource substitutes
it into the rules, and the hidden tests are **generated per variant** by `tests/gen_hidden.py`
instead of being fixed files. A copied solution that hard-codes someone else's parameter fails.
It also shows what that option costs: the professor writes a generator plus a checker instead of
a directory of cases, and the runner invokes the generator once per submission.

Domain: weighted interval scheduling (a classic DP). Type A, so the student's own `solve.py` is
graded deterministically, once, plus the ledger gate.

## Interface contract

Input: `{"variant": "<string>", "jobs": [{"id","start","end","weight","class"}, ...]}`
Output: `{"total": <int>, "chosen": [<ids in start order>]}`

The variant travels inside the input JSON so `solve.py` is self-contained and the tests are
self-describing. Several optimal schedules may exist, so every category directory carries a
`check.py` that validates feasibility under the variant's rules and equality of the total, rather
than comparing the chosen list. Each generated directory also carries `variant.json` (the
variant and its g) for the checker's fallback and for a TA reading the tests.

## The twist

Two rules replace the textbook "next.start >= prev.end", both parameterised by a cooldown gap g:

1. **Cooldown.** A class `S` job must start at least g after the previous chosen job ends.
2. **Priority exemption.** A class `P` job needs no gap, only non-overlap.

Only the later job's class matters for a pair.

**How g derives from the variant.** `g = 1 + (sum of character codes of the variant) mod 4`, so
g is 1–4. The resource page states the formula in words with a worked example for `demo`
(sum 421, 421 mod 4 = 1, g = 2). The page cannot compute g for the student because the server only
substitutes the string; the student (or their harness) computes it. Values used here:

| variant | g |
|---|---|
| demo | 2 |
| JKL333444 | 3 |
| ABC123456 | 4 |

Against the twist checklist: not online; under a page; breaks the canonical DP on identifiable
inputs (the two twist categories are filtered so the canonical optimum is infeasible); requires
understanding the DP's compatibility boundary to implement in O(n log n); testable through the
contract alone; hinted by the public tests (demo variant) but not exhausted by them.

## Categories and weights

| Category | Cases | Weight | Notes |
|---|---|---|---|
| basic | 5 | 1 | jobs in slots spaced beyond any g; canonical solution passes |
| overlaps | 5 | 1 | dense in-slot overlaps, same spacing; canonical passes |
| twist_cooldown | 6 | 1 (twist) | S-only, filtered so the canonical schedule is infeasible |
| twist_class | 6 | 1 (twist) | mixed P/S, filtered so the exemption changes the optimum and canonical is infeasible |
| grad_large | 4 | 1 (grad only) | 3,000 jobs, 10 s limit; the O(n log n) reference takes ~0.03 s |

Twist categories carry half of the non-graduate weight, as the framework requires.

## Files

```
project.json                  type A, variants.generator = tests/gen_hidden.py
resource/index.md             published resource; {{VARIANT}}, {{NONCE}}, {{BASE_URL}} substituted by the ledger server
tests/check.py                the checker copied into every category directory
tests/gen_hidden.py           --variant X --out DIR [--public]; deterministic in X
tests/public/                 generated for variant "demo" with --public (no grad_large)
reference/solution/solve.py   O(n log n) DP with the twist; source of expected outputs
canonical/solve.py            textbook DP, twist ignored
handout.md                    filled Type A handout
submissions/JKL333444/        sample student submission (solve.py, variant.txt, PROCESS.md, WRITTEN.md)
variants.csv                  professor's assignment of variants
```

## How to run

```
# public tests (what students run; demo variant)
python3 ../../tools/run_tests.py --solution reference/solution --tests tests/public

# generate a student's hidden tests by hand
python3 tests/gen_hidden.py --variant JKL333444 --out /tmp/hidden-JKL333444

# TA batch: the runner reads the variant from variants.csv and calls the generator per submission
python3 ../../tools/runner.py --project project.json --submissions submissions --type A --out runs/
python3 ../../tools/grade.py --project project.json --runs runs/ --status status.csv

# ledger server for the resource (from the framework root)
python3 tools/ledger_server.py --resource examples/04-scheduling-type-a-variants/resource \
    --ledger ledger.tsv --nonce <NONCE> --port 8080 --base-url http://host.docker.internal:8080
```

## Professor workflow for variants

1. Fill `variants.csv` (`student_id,variant`). The simplest variant is the student ID itself; pairs
   use the first partner's ID (the sample row `MNO777888+PQR999000,MNO777888`).
2. Tell each student their URL: `.../?v=<variant>`. The handout says the public tests are for
   `demo`, not their variant.
3. The **professor's `variants.csv` roster decides** each student's variant. A `variant.txt`
   inside a submission is ignored, so a student cannot choose an easier variant by editing it.
   Students are told their variant through the resource URL the handout gives them.
4. The hidden suite is not a directory in the repo; it is whatever `gen_hidden.py` produces for
   the variant. After grading, release the generator (it is deterministic) instead of the cases.
5. Calibration: run the reference solution against generated tests for at least two variants
   (done below) and the canonical solution against one, before release.

## Verification record (2026-09-08)

Reference solution, generated hidden tests, variant `demo` (g = 2):
`{'basic': (5, 5), 'grad_large': (4, 4), 'overlaps': (5, 5), 'twist_class': (6, 6), 'twist_cooldown': (6, 6)}`

Reference solution, variant `ABC123456` (g = 4):
`{'basic': (5, 5), 'grad_large': (4, 4), 'overlaps': (5, 5), 'twist_class': (6, 6), 'twist_cooldown': (6, 6)}`

Canonical solution (twist ignored), variant `demo` and `ABC123456`, identical result:
`{'basic': (5, 5), 'grad_large': (0, 4), 'overlaps': (5, 5), 'twist_class': (0, 6), 'twist_cooldown': (0, 6)}`
The twist is load-bearing: canonical passes every non-twist case and no twist case.

Reference vs public: `{'basic': (2, 2), 'overlaps': (1, 1), 'twist_class': (1, 1), 'twist_cooldown': (2, 2)}`
Canonical vs public: `{'basic': (2, 2), 'overlaps': (1, 1), 'twist_class': (0, 1), 'twist_cooldown': (0, 2)}`

grad_large wall time per case for the reference: 0.029 s (limit 10 s).

**The sample submission fails one public test on purpose:** it scores 5/6 on the public suite
(`twist_class`), because it is the worked example of candor — its WRITTEN.md states the
limitation and predicts exactly that failure — so it would *not* earn the milestone, which
requires a clean public suite; do not "fix" it, and if you copy it for a rehearsal expect
`milestone 0`.

Sample submission `JKL333444` (implements the cooldown, omits the priority exemption; its
WRITTEN.md predicts the twist_class failure), run through the runner with `--type A --no-sandbox`,
which exercised the per-variant generator path, then `grade.py`:

```
student_id,status,grad,best_slot,hidden_score,basic_pass,overlaps_pass,twist_cooldown_pass,twist_class_pass,grad_large_pass,milestone,written_raw,written_score,total,note
JKL333444,graded,0,A,52.5,5/5,5/5,6/6,0/6,,,,,52.5,          # undergraduate
JKL333444,graded,1,A,42.0,5/5,5/5,6/6,0/6,0/4,,,,42.0,       # same submission graded as graduate
```

`prescan.py` on the submission: `OK JKL333444 words=1` (solution code does not count toward the specification cap).

The handout's worked example was produced by the reference solution: `{"total": 14, "chosen": ["a", "c"]}`.

**Not verified here:** the sandboxed (Docker) path of the runner and any regeneration through
OpenCode, since this example is Type A and the machine used for verification had no OpenCode
install. The ledger server's substitution of `{{VARIANT}}` from `?v=` was exercised by the
framework's own tool tests, not from this directory.

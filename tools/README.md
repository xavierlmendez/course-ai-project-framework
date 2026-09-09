# Tools

Python 3 standard library plus Docker and Ollama. A TA can read every file in one sitting.

| Tool | Role |
|---|---|
| `run_tests.py` | Runs interface-contract tests against one solution directory. Used by students (public suite), by the milestone, and by the runner inside the sandbox (hidden suite). Given `--project project.json` it enforces each category's declared equivalence policy and reports it in the summary. |
| `runner.py` | TA batch runner. Type B: K sandboxed regenerations per submission, then hidden tests. Type A: hidden tests once. Also creates the pinned slot models (`--create-slots`). Resumable. |
| `grade.py` | Turns runner records plus `status.csv`, `written.csv`, `milestone.csv` into `gradebook.csv`. Refuses a `status.csv` with no `grad` column, refuses a written dimension outside 0–3, and marks a row `incomplete` rather than emitting a total that silently omits a component. |
| `combine_parts.py` | Combines per-part gradebooks. Each part contributes only its **hidden** score, weighted; the milestone and written component are course-level and added once. |
| `prescan.py` | Flags lines in specifications the safety read must look at closely. Not a safety control. |
| `ledger_server.py` | Serves the published resource and the write-only ledger endpoint. Reference implementation; port the one route into an existing site if you have one. |
| `sandbox/` | Docker image: Python, a **pinned** OpenCode, curl, and an outbound allowlist of host:port pairs. Hidden tests are staged root-only; the graded solution runs unprivileged. |
| `../tests/` | `python3 -m unittest discover -s tests`. Every test names the finding it guards. No Docker, model or network needed. |
| `../scripts/rehearsal.py` | Grades a fixture cohort end to end and prints the arithmetic beside the gradebook, so the totals can be checked by hand. |
| `../scripts/review_checks.py` | The deterministic checks over the examples and the repo. |

## Layout of a project directory

```
project.json
seeds.secret.json           {"seeds": [n1, n2, n3]}   never committed, secret until grades are out
resource/index.md           the published resource; {{NONCE}}, {{VARIANT}}, {{BASE_URL}} substituted
tests/public/<cat>/NNN.in.json + NNN.out.json     (or check.py in the category dir)
                            argv-files contract instead: NNN.args ("{in} {out} 3"), NNN.in.txt,
                            NNN.stdout.txt (+ NNN.outfile.txt); see run_tests.py docstring
tests/hidden/<cat>/...      one directory per category named in project.json
                            check.py is REQUIRED in any category whose policy is not
                            "strict" and must be absent from one that is: the checker is
                            the only thing that realises a policy, so the declaration and
                            the directory have to agree. `run_tests.py --project` and
                            `scripts/review_checks.py` both refuse a category where they
                            do not
tests/gen_hidden.py         only for variant projects: --variant X --out DIR writes tests/hidden-shaped dirs
reference/SPEC.md           Type B reference specification (the calibration gate and appeals key)
reference/solution/solve.py the professor's own solution, used to produce expected outputs
canonical/solve.py          textbook solution with the twist ignored; must score low on twist categories
handout.md                  filled template
submissions/<id>/           SPEC.md (+ supporting files), PROCESS.md, WRITTEN.md   [Type B]
                            solve.py (+ files), PROCESS.md, WRITTEN.md              [Type A]
                            variant.txt                                            [variant projects]
```

## `project.json`

```jsonc
{
  "name": "morris-b",                   // used to name slot models: ref-morris-b-slot1..3
  "type": "B",                          // "A" or "B"
  "entry": "solve.py",                  // the file the harness must produce
  "spec": "SPEC.md",                    // the specification file the harness is told to read.
                                        //   Multi-part: "SPEC-part-I.md" and so on, one per part
  "part": "I",                          // optional. Declaring it puts grade.py in hidden-only
                                        //   mode: the part scores hidden marks only, and
                                        //   combine_parts.py adds milestone and written once
  "python": "python3",
  "resource_host": "host.docker.internal",          // the published resource's host …
  "resource_port": 8080,                            // … and its port. The sandbox allowlist is
                                                    //   host:port pairs, never a bare host
  "ollama_host": "http://host.docker.internal:11434",
  "base_model": "qwen2.5-coder:14b",
  "k": 3,
  "temperatures": [0.2, 0.6, 1.0],
  "seeds_file": "seeds.secret.json",
  "regeneration_timeout_s": 1200,       // set to 2x the reference specification's slowest passing run
  "test_timeout_s": 10,
  "hidden_tests": "tests/hidden",
  "public_tests": "tests/public",
  "hidden_points": 70, "milestone_points": 10, "written_points": 20,
  "categories": {                       // twist categories' weights must sum to half of all non-grad weights
                                        // every category also declares its equivalence
                                        //   policy (framework.md section 9). Required:
                                        //     "strict"    exact comparison; no check.py
                                        //     "estimate"  equal quality, not equal output
                                        //     "ab"        same move/answer as the reference
                                        //     "valid"     any output the rules admit
                                        //   Anything but "strict" is realised only by a
                                        //   check.py in the category directory
    "basic":        {"weight": 1, "policy": "strict"},
    "twist_rule":   {"weight": 2, "twist": true, "policy": "strict"},
    "grad_hard":    {"weight": 1, "grad_only": true, "policy": "valid"}
  },
  "wrapper_prompt": "Read SPEC.md ... {entry} ...",   // optional; identical for every student
  "sandbox_image": "harness-sandbox",
  "sandbox_memory": "2g",
  "slot_prefix": "ref-morris-b-slot",   // optional; defaults to "ref-<name>-slot"
  "extra_allow_endpoints": [],          // optional; extra "host:port" pairs for the sandbox
  "variants": {                         // optional, for per-student variants
    "generator": "tests/gen_hidden.py",
    "roster": "variants.csv"            // student_id,variant. The roster decides; a
                                        //   variant.txt inside a submission is ignored
  }
}
```

## Cohort files

```
status.csv     student_id,status,grad,note      # grad is required: 1 for graduate rows
written.csv    student_id,accuracy,twist,candor[,prediction]    # 0-3 each
milestone.csv  student_id,milestone             # 1 or 0
variants.csv   student_id,variant               # variant projects only
```

## Ledger file

Tab-separated, one entry per line, header lines start with `#`:

```
utc_timestamp    student_ids (ABC123456 or ABC123456+DEF654321)    run_tag    variant    client_ip
```

Filter grading entries with `grep -P '\tgrading-k[123]\t' ledger.tsv`.

## What the sandbox allows

Outbound traffic is restricted to the **host and port** pairs the task needs: the published
resource and the model server. A bare host would expose every service on the grading machine,
including the model server's management API, which can read the secret seeds and overwrite the
pinned slot models. DNS is allowed only to the container's own resolvers, because allowing port
53 to any destination is a tunnel through the allowlist. IPv6 is dropped entirely.

The hidden tests are mounted inside `/root`, which the graded user cannot traverse, and staged
to a root-only copy for the test runner. `run_tests.py` runs as root there and drops to the
unprivileged `runner` user for each solution, so a solution cannot read an expected output
instead of computing it. That drop is the default whenever the runner is root; `--run-as root`
opts out deliberately.

The OpenCode version is pinned in the Dockerfile (`ARG OPENCODE_VERSION`). This is a correctness
control, not hygiene: the best-of-K temperature schedule reaches the model only because this
version sends no sampling parameters of its own. `runner.py --verify-slots` asks the model server
what each slot's effective temperature and seed are and fails loudly if the schedule is not
reaching it; a graded batch runs that check automatically.

## What the runner will refuse

- `--submission` pointing at a directory containing `project.json`. That is a project, not a
  submission, and copying it into the container would hand the harness the hidden tests, the
  reference solution and `seeds.secret.json`.
- An `--out` directory inside the submission tree, which copies a run into itself.
- `--slot` outside 1..k.
- A submission with no specification file.

Only the specification and the data files it names by filename are copied into the working
directory. Files ending in the entry point's extension are never copied, so a student cannot
ship a finished solution and be graded on it.

## Records and resume

A grading run writes `runs/<id>/k<N>.json`. Any other run tag writes `runs/<id>/<tag>-k<N>.json`,
so an **appeal** is a record of its own: it neither collides with the grading record nor is
mistaken for one already done. `grade.py` considers every complete record and takes the best.

A slot whose regeneration failed because the **environment** was broken (model server down,
docker unreachable, disk full) is written with `"complete": false` and an `incomplete_reason`,
and is not scored. Re-running the same command retries it. Three such failures in a row abort
the batch, on the grounds that the machine, not the cohort, is what needs fixing.

## Commands

```
docker build -t harness-sandbox tools/sandbox/
python3 tools/runner.py --project project.json --create-slots
python3 tools/ledger_server.py --resource resource/ --ledger ledger.tsv --nonce <NONCE> --port 8080 \
        --base-url http://host.docker.internal:8080
python3 tools/runner.py --project project.json --verify-slots   # is the schedule reaching the model?
python3 tools/prescan.py submissions/ --project project.json
python3 tools/runner.py --project project.json --submissions submissions/ --status status.csv --out runs/
python3 tools/grade.py --project project.json --runs runs/ --status status.csv --written written.csv \
        --milestone milestone.csv > gradebook.csv

# multi-part: grade each part (hidden only), then combine once
python3 tools/grade.py --project part-I/project.json  --runs part-I/runs  --status status.csv > gb-I.csv
python3 tools/grade.py --project part-II/project.json --runs part-II/runs --status status.csv > gb-II.csv
python3 tools/combine_parts.py --parts parts.json --written written.csv --milestone milestone.csv \
        gb-I.csv gb-II.csv > gradebook.csv

# check the tools themselves
python3 -m unittest discover -s tests
python3 scripts/rehearsal.py
```

## Things to verify during the calibration run

These are documented behaviours of the tools involved that this repository has not exercised end to end:

- The OpenCode configuration shape written by `runner.py` (`provider.ollama` via `@ai-sdk/openai-compatible`, `permission` block) against the current OpenCode docs.
- That `opencode run --format json` exits non-zero on failure and finishes without a TTY.
- That the Ollama Modelfile `PARAMETER seed` is honoured by the `/v1` endpoint OpenCode uses.
- That `host.docker.internal` resolves on the grading machine (Linux needs the `--add-host` flag the runner already passes).

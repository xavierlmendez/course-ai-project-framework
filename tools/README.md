# Tools

Python 3 standard library plus Docker and Ollama. A TA can read every file in one sitting.

| Tool | Role |
|---|---|
| `run_tests.py` | Runs interface-contract tests against one solution directory. Used by students (public suite), by the milestone, and by the runner inside the sandbox (hidden suite). Given `--project project.json` it enforces each category's declared equivalence policy and reports it in the summary. |
| `runner.py` | TA batch runner. Type B: K sandboxed regenerations per submission, then hidden tests. Type A: hidden tests once. Also creates the pinned slot models (`--create-slots`), and gives students one practice command (`--practice`). Both stop with the URL they tried if the model server is unreachable, and a missing `opencode` or `docker` binary gives a sentence naming what to install, not a traceback. Resumable. |
| `grade.py` | Turns runner records plus `status.csv`, `written.csv`, `milestone.csv` into `gradebook.csv`. Refuses a `status.csv` with no `grad` column, refuses a written dimension outside 0–3, and marks a row `incomplete` rather than emitting a total that silently omits a component. Its `records` column says how many complete records the row was scored from, with the incomplete ones in brackets (`3`, `2 (1 never completed)`). |
| `grade_all.py` | Grades a whole project, single-part or multi-part, in one command. Replaces the shell loop, which word-split differently in bash and zsh and silently continued past a part that was never run. Given `--submissions DIR` (the course-level submissions directory) it runs the fan-out itself first, so the per-program directories always match what the students handed in. Writes one intermediate gradebook per part, `gb-<program>.csv`, beside the project or under `--work`. |
| `combine_parts.py` | Combines per-part gradebooks. Each part contributes only its **hidden** score, weighted; the milestone and written component are course-level and added once. Columns: `student_id`, `grad`, `<part>_hidden` and `<part>_records` per part, then `hidden_score`, `milestone`, `written_raw`, `written_score`, `total`, `status`, `note`. There is one course-level `status` and no `<part>_status`: that column copied the course-level status into every program, so an appeal scoped to one part read `appeal` on all eight. |
| `milestone.py` | `record` (student) runs the public suite and writes a milestone record; on a Type B project it requires the runner record of a completed regeneration and embeds it as the record's `harness` block. `check` (TA) validates submitted records into `milestone.csv`, refusing a Type B record with no harness evidence. |
| `fan_out.py` | Turns the **student layout** of a multi-part submission (`submissions/<id>/<program>/SPEC.md`, plus one `WRITTEN.md` and one `PROCESS.md` at the top) into the per-program `part-<program>/submissions/<id>/` directories the runner reads, copying the course-level pages into each. One row per student: programs present/missing, words per `SPEC.md`. Exit 1 with a named reason for any layout problem; `--check` validates without writing. |
| `prescan.py` | Flags lines in specifications the safety read must look at closely. Not a safety control. `--course DIR` takes the project directory in either shape: with `parts.json` it scans the course-level submissions of a multi-part project instead of one part's, and without one it scans that single-part project's own `submissions/` with its `project.json`. One row per student either way, and it is where the single `WRITTEN.md` and `PROCESS.md` are checked. A **Type A** project has no specification, so its rows read `words=n/a` and the 1,500-word cap is not applied; the page caps still are. |
| `ledger_server.py` | Serves the published resource and the write-only ledger endpoint. `--project project.json` takes its resource directory, ledger file, nonce and port from the project, which is the form a handout can give a student. A busy port exits with one sentence — `port N is already in use: another resource server is probably still running (stop it, or pass --port to use another port)` — not a traceback. Reference implementation; port the one route into an existing site if you have one. |
| `sandbox/` | Docker image: Python, a **pinned** OpenCode, curl, and an outbound allowlist of host:port pairs. Hidden tests are staged root-only; the graded solution runs unprivileged. |
| `../tests/` | `python3 -m unittest discover -s tests`. Every test names the finding it guards. No Docker, model or network needed. |
| `../scripts/rehearsal.py` | Grades a fixture cohort end to end and prints the arithmetic beside the gradebook, so the totals can be checked by hand. |
| `../scripts/review_checks.py` | The deterministic checks over the examples and the repo. |

**When the binary checks happen.** They run before anything is written, because a practice run
used to create slot models and print "slots ready" before reporting that `opencode` was missing:

- practice mode, and any other non-sandboxed Type B regeneration, checks `opencode` and then
  `ollama` **before** writing `seeds.practice.json` or creating any slot;
- a sandboxed run checks `docker` instead, and first;
- `--create-slots` checks the `ollama` binary **and** that the model server answers, both before
  the first Modelfile is written;
- `--dry-run` skips all of these: it prints the command lines and runs nothing.

## Layout of a project directory

```
project.json
seeds.secret.json           {"seeds": [n1, n2, n3]}   never committed, secret until grades are out
seeds.practice.json         written by --practice when the secret seeds are absent; never committed
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

A multi-part project keeps one **course-level** `submissions/<id>/` in the student layout —
`<program>/SPEC.md` per program, one `WRITTEN.md` and one `PROCESS.md` at the top — and
`fan_out.py` derives the per-program `part-<program>/submissions/<id>/` from it. Those derived
directories are generated output: `examples/01-morris-type-b/part-*/submissions/` are gitignored
and are rebuilt by the fan-out, so nothing there should be edited by hand.

## `project.json`

Every key the tools read is listed below, and the value shown is the default where there is one, so
a project that omits a key behaves as written here. Keys marked *optional* have no default and are
simply absent unless the professor sets them.

```jsonc
{
  "name": "morris-b",                   // used to name slot models: ref-morris-b-slot1..3
  "type": "B",                          // "A" or "B"
  "entry": "solve.py",                  // the file the harness must produce
  "nonce": "A1B2C3D4E5F6",              // printed on the resource page and required by the
                                        //   ledger. Lives here only; ledger_server.py --project
                                        //   reads it, so rotation changes one line. Omit it and
                                        //   the server mints and prints a random practice nonce
  "spec": "SPEC.md",                    // the specification file the harness is told to read.
                                        //   Multi-part: "SPEC-part-I.md" and so on, one per part
  "part": "I",                          // optional. Declaring it puts grade.py in hidden-only
                                        //   mode: the part scores hidden marks only, and
                                        //   combine_parts.py adds milestone and written once
  "python": "python3",
  "resource_host": "host.docker.internal",          // the published resource's host …
  "resource_port": 8080,                            // … and its port. The sandbox allowlist is
                                                    //   host:port pairs, never a bare host
  "resource_dir": "resource",                       // optional; where ledger_server.py --project
                                                    //   finds the page. Relative to project.json
  "ledger": "ledger.tsv",                           // optional; same, for ledger_server.py --project.
                                                    //   The server refuses a path inside a repository
                                                    //   unless --allow-in-repo is given
  "ollama_host": "http://host.docker.internal:11434",   // as the *sandbox* reaches it. Used
                                        //   verbatim only inside the sandbox: the OpenCode
                                        //   baseURL, the sandbox allowlist, OLLAMA_HOST in
                                        //   the container
  "ollama_host_local": null,            // optional: as *this machine* reaches it, when the
                                        //   model server is not on the docker host (a course
                                        //   server). A container-only name is translated to
                                        //   loopback automatically. Everything that runs on
                                        //   the host uses this address: --create-slots and
                                        //   every other `ollama` CLI call (OLLAMA_HOST is set
                                        //   for them), --verify-slots, and the OpenCode
                                        //   baseURL of a --no-sandbox / --practice run. A
                                        //   student with a local Ollama therefore edits
                                        //   nothing; a student on the course server sets this
                                        //   one key
  "base_model": "qwen3:14b",
  "num_ctx": 32768,                     // context window pinned into every slot Modelfile
                                        //   (PARAMETER num_ctx). The agent loop's tool
                                        //   schemas do not fit Ollama's 4096 default;
                                        //   measured 2026-09-08/09. --verify-slots checks it
  "thinking": "off",                    // "off" (default): the slot Modelfile carries the base
                                        //   model's chat template patched to disable qwen3's
                                        //   thinking mode, because a thinking model narrates its
                                        //   plan inside <think> and ends the turn without calling
                                        //   a tool, so the agent loop never gets past the first
                                        //   step (R620, 2026-09-09, D-007). The patch is applied
                                        //   to whatever `ollama show --template <base_model>`
                                        //   returns and --create-slots stops if that template
                                        //   carries no qwen3 thinking switch.
                                        //   "default": the template is left untouched — use it
                                        //   for a base model with no thinking mode.
                                        //   --verify-slots checks the slot's template too and
                                        //   says "slot N still thinks" if it was created before
                                        //   this patch. `PARAMETER think false` and a `"think":
                                        //   false` request field are both dead ends: Modelfiles
                                        //   reject the parameter and Ollama's /v1 endpoint, the
                                        //   one OpenCode uses, ignores the field
  "k": 3,
  "temperatures": [0.2, 0.6, 1.0],
  "seeds_file": "seeds.secret.json",
  "regeneration_timeout_s": 1200,       // set to 2x the reference specification's slowest passing run.
                                        //   1200 is a GPU number. On the CPU-only R620 a full
                                        //   Type B run took 28 minutes without the course page and
                                        //   was still working at 90 minutes with it (2026-09-09),
                                        //   so a CPU grading box needs hours, not twenty minutes
  "test_timeout_s": 10,
  "hidden_tests": "tests/hidden",
  "public_tests": "tests/public",
  "hidden_points": 70, "milestone_points": 10, "written_points": 20,
  "all_twist": false,                   // set true only for a part whose categories are ALL twist
                                        //   categories; review_checks.py then accepts it
  "categories": {                       // the twist-half rule: the twist categories' weights sum to
                                        //   exactly half of the non-graduate weights; a part whose
                                        //   categories are all twist categories is allowed and the
                                        //   rule then applies trivially (all of the non-grad weight
                                        //   is twist, so the professor must either add a non-twist
                                        //   category or accept that the part is entirely twist, and
                                        //   say which in the handout)
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
milestone.csv  student_id,milestone,note        # 1 or 0, written by milestone.py check
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

## The milestone record

`milestone.py record` writes `milestone-<project name>.json` — `milestone-<name>-<part>.json` when
the project sets a `part`, with runs of non-alphanumeric characters collapsed to `-`. `--out` is
optional and overrides it. Two projects checked out side by side both defaulted to `milestone.json`
and the second record overwrote the first, which is why the default carries the project's name.

The record's `harness` block is what `check` reads:

```jsonc
// Type A: no harness runs, and the record says so rather than naming a model
"harness": {"type": "A", "model": null,
            "note": "Type A: code graded directly; no harness run"}

// Type B: the evidence that the code measured came out of a run
"harness": {"model": …, "run_tag": …, "slot": …, "harness_exit": …,
            "wall_s": …, "entry_present": true, "complete": true, "record": …}
```

`check` refuses a Type B record with no harness block ("no harness evidence") and a **Type A**
record that names a model, since no model was ever loaded.

The runner record `record --regeneration` accepts must carry `run_tag` (the tag **with** the slot suffix, exactly as the runner writes it: `practice-k1`, `grading-k2`; the work directory is `<run_tag>-work`), `complete`, `dry_run`, and
inside its `regeneration` block `entry_present`, `harness_exit` and `wall_s`, plus `slot` on the
record; anything missing those is not a runner record and is refused by name.

## Records and resume

### What a grading record holds

One record per run, written by `runner.py`. The fields the other tools read:

- `submission` — the submission directory's name, which is the gradebook key.
- `type` — `"A"` or `"B"`: whether the record is a direct run of submitted code or a
  regeneration through the harness. `milestone.py` and `grade.py` branch on it.
- `slot`, `temperature` — Type B only: which of the K slots this run was, and the
  temperature that slot's model was pinned to. `grade.py` reports the best slot.
- `seed_recorded: false` — always false, and present to say so: the seed value is
  deliberately **not** stored, because a record travels with an appeal packet and the
  seeds are secret until grades are released.
- `run_tag` — the tag **with** the slot suffix (`grading-k2`, `practice-k1`); the working
  directory is `<run_tag>-work`.
- `started`, `ended`, `complete`, `incomplete_reason`, `dry_run` — when it ran, whether it
  finished, why not, and whether it was a `--dry-run` (those are also named `*.dry.json`).
- `tests_dir` — the absolute path of the hidden suite this run was scored against, so a
  record says which tests produced its numbers. `null` when none was resolved.
- `regeneration` — Type B only: `entry_present`, `harness_exit`, `wall_s`, the model and
  the command. `milestone.py` reads it as harness evidence.
- `tests` — the hidden-suite result, below.

### The `tests` block

It is `run_tests.py --json`'s output, embedded verbatim (`{"dry_run": true}` for a dry run,
or `{"solution_started": false, "categories": {}, "error": …}` if the runner could not parse
it). `grade.py` reads only `solution_started` and `categories[*].pass` / `.total`.

```jsonc
{"solution_started": true,          // false when the entry point was missing or the
                                    // policy check refused; then "error" says which
 "categories": {
   "evaluations_count": {
     "pass": 3,                     // cases that passed
     "total": 4,                    // cases discovered in that category
     "policy": "strict",            // the equivalence policy in force, present only when
                                    // run_tests.py was given --project
     "cases": [                     // one entry per case, for reading a failure
       {"name": "001", "pass": false, "why": "output mismatch", "wall_s": 0.12}]}}}
```

A category that exists in `project.json` but has no cases on disk does not appear here at
all; `grade.py` then leaves it out of both sums rather than scoring it zero.


Paths below are the **grading** layout, where the run directory is the submission's id: a grading
run writes `runs/<id>/k<N>.json` beside its working directory `runs/<id>/grading-k<N>-work`.
A student's own run is named after their submission directory instead — `mywork/part-I-opening`
gives `runs/part-I-opening/practice-k1.json` beside `runs/part-I-opening/practice-k1-work`, which
is the form the handouts use.
Any other run tag writes `runs/<id>/<tag>-k<N>.json` beside `runs/<id>/<tag>-k<N>-work`, so an
**appeal** is a record of its own: it neither collides with the grading record nor is mistaken for
one already done. `grade.py` considers every complete record and takes the best.

`--dry-run` prints the command lines and runs nothing. Its records are kept — they are the easiest
way to see exactly what would be executed — but named apart: `runs/<id>/<tag>-k<N>.dry.json` beside
`runs/<id>/<tag>-k<N>-dry-work`, and carrying `"dry_run": true`. `grade.py` and `milestone.py` skip
every `*.dry.json`, so a dry run can never be mistaken for a slot that ran, or counted as one that
never finished.

A slot whose regeneration failed because the **environment** was broken (model server down,
docker unreachable, disk full) is written with `"complete": false` and an `incomplete_reason`,
and is not scored. Re-running the same command retries it. Three such failures in a row abort
the batch, on the grounds that the machine, not the cohort, is what needs fixing.

## Commands

```
docker build -t harness-sandbox tools/sandbox/
python3 tools/runner.py --project project.json --create-slots   # OLLAMA_HOST is set from the
                                                                # project; pins temperature,
                                                                # seed, num_ctx and the no-think
                                                                # TEMPLATE per slot
python3 tools/ledger_server.py --project project.json \
        --base-url http://host.docker.internal:8080   # port comes from resource_port
python3 tools/runner.py --project project.json --verify-slots   # is the schedule reaching the model?
python3 tools/fan_out.py --project . --submissions submissions   # multi-part: student layout
                                                                 # -> part-*/submissions/<id>/
python3 tools/prescan.py --course .                              # either shape: with parts.json the
                                                                 # course tree, without it the project's
                                                                 # own submissions/; one row per student
python3 tools/prescan.py submissions/ --project project.json     # one program's submissions
python3 tools/runner.py --project project.json --submissions submissions/ --status status.csv --out runs/
python3 tools/grade.py --project project.json --runs runs/ --status status.csv --written written.csv \
        --milestone milestone.csv > gradebook.csv

# the whole project in one command, single-part or multi-part
python3 tools/grade_all.py --project . --submissions submissions --status status.csv \
        --written written.csv --milestone milestone.csv > gradebook.csv

# the milestone
# Type A: --solution is the directory holding the code being submitted.
python3 tools/milestone.py record --project project.json --solution <dir> \
        --student-id ABC123456                               # student; writes
                                                             # milestone-<name>.json
# Type B: --regeneration is REQUIRED and --solution must be that record's own work directory.
# The record must be a completed runner record (not a *.dry.json one) whose regeneration
# produced the entry point; the milestone embeds its model, run tag, slot, wall time and file
# name as the `harness` block, and `milestone.py check` refuses a Type B record without one
# ("no harness evidence"). Anything else — a mistyped path, hand-written code beside a real
# run, a dry-run record — is refused with a message saying which.
python3 tools/milestone.py record --project project.json \
        --solution runs/ABC123456/practice-k1-work \
        --regeneration runs/ABC123456/practice-k1.json \
        --student-id ABC123456                               # TA/grading layout: the run
                                                             # directory is the submission id.
                                                             # A student's own run is named
                                                             # after their directory instead:
                                                             # runs/<dir name>/practice-k1.json
python3 tools/milestone.py check --project project.json --records milestone-records/ \
        --status status.csv > milestone.csv                   # TA

# the commands a student runs: no secret seeds, no prepared slot models, public suite
python3 tools/ledger_server.py --project project.json --allow-in-repo   # practice ledger, port from the project
python3 tools/runner.py --project project.json --submission <dir> --practice

# check the tools themselves
python3 -m unittest discover -s tests -p "test_[a-r]*.py"   # fast suite; test_sandbox needs Docker
python3 scripts/rehearsal.py
```

### Every flag, per tool

Each tool's own `--help` is the authority; this is the same list in one place.

| Tool | Flags |
|---|---|
| `runner.py` | `--project` (required) · `--submissions DIR` or `--submission DIR` · `--out` (default `runs`) · `--status` · `--run-tag` (default `grading`) · `--slot N` · `--tests DIR` · `--type A\|B` · `--create-slots` · `--verify-slots` · `--skip-slot-check` · `--dry-run` · `--no-sandbox` · `--practice` |
| `run_tests.py` | `--solution` `--tests` (required) · `--entry` (default `solve.py`) · `--timeout` (default 10) · `--python` · `--json` · `--project` · `--run-as` |
| `milestone.py record` | `--project` `--solution` `--student-id` (required) · `--regeneration` (required for Type B) · `--out` (default `milestone-<project name>.json`, or `milestone-<name>-<part>.json`) |
| `milestone.py check` | `--project` `--records` (required) · `--status` |
| `grade.py` | `--project` `--runs` (required) · `--status` · `--written` · `--milestone` · `--hidden-only` |
| `grade_all.py` | `--project DIR` `--status` (required) · `--submissions DIR` (course-level; runs the fan-out first) · `--written` · `--milestone` · `--work` |
| `fan_out.py` | `--project DIR` `--submissions DIR` (required) · `--check` (validate, write nothing) |
| `combine_parts.py` | `--parts` (required) · `--written` · `--milestone` · `--hidden-points` (70) · `--milestone-points` (10) · `--written-points` (20) · then the per-part gradebooks, in `parts.json` order |
| `prescan.py` | `SUBMISSIONS_DIR` (positional) or `--course DIR` · `--project` · `--allow HOST …` · `--cap` (default 1500) · `--page-cap` (default 600) |
| `ledger_server.py` | `--project` (supplies the four below) or `--resource` `--ledger` `--nonce` · `--port` · `--bind` · `--base-url` · `--allow-in-repo` |

## Things to verify during the calibration run

These are documented behaviours of the tools involved that this repository has not exercised end to end:

- The OpenCode configuration shape written by `runner.py` (`provider.ollama` via `@ai-sdk/openai-compatible`, `permission` block) against the current OpenCode docs.
- That `opencode run --format json` exits non-zero on failure and finishes without a TTY.
- That the Ollama Modelfile `PARAMETER seed` is honoured by the `/v1` endpoint OpenCode uses.
- That `host.docker.internal` resolves on the grading machine (Linux needs the `--add-host` flag the runner already passes).

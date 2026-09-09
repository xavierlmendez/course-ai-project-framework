# Tools

Python 3 standard library plus Docker and Ollama. A TA can read every file in one sitting.

| Tool | Role |
|---|---|
| `run_tests.py` | Runs interface-contract tests against one solution directory. Used by students (public suite), by the milestone, and by the runner inside the sandbox (hidden suite). |
| `runner.py` | TA batch runner. Type B: K sandboxed regenerations per submission, then hidden tests. Type A: hidden tests once. Also creates the pinned slot models (`--create-slots`). Resumable. |
| `grade.py` | Turns runner records plus `status.csv`, `written.csv`, `milestone.csv` into `gradebook.csv`. |
| `combine_parts.py` | Weights per-part gradebooks into one for multi-part projects (`parts.json` holds the weights). |
| `prescan.py` | Flags lines in specifications the safety read must look at closely. Not a safety control. |
| `ledger_server.py` | Serves the published resource and the write-only ledger endpoint. Reference implementation; port the one route into an existing site if you have one. |
| `sandbox/` | Docker image: Python, OpenCode, curl, outbound firewall allowlist. |

## Layout of a project directory

```
project.json
seeds.secret.json           {"seeds": [n1, n2, n3]}   never committed, secret until grades are out
resource/index.md           the published resource; {{NONCE}}, {{VARIANT}}, {{BASE_URL}} substituted
tests/public/<cat>/NNN.in.json + NNN.out.json     (or check.py in the category dir)
                            argv-files contract instead: NNN.args ("{in} {out} 3"), NNN.in.txt,
                            NNN.stdout.txt (+ NNN.outfile.txt); see run_tests.py docstring
tests/hidden/<cat>/...      one directory per category named in project.json
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
  "entry": "solve.py",
  "python": "python3",
  "resource_host": "host.docker.internal",          // allowed outbound host for the published resource
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
    "basic":        {"weight": 1},
    "twist_rule":   {"weight": 2, "twist": true},
    "grad_hard":    {"weight": 1, "grad_only": true}
  },
  "wrapper_prompt": "Read SPEC.md ... {entry} ...",   // optional; identical for every student
  "sandbox_image": "harness-sandbox",
  "sandbox_memory": "2g",
  "variants": {"generator": "tests/gen_hidden.py"}    // optional
}
```

## Ledger file

Tab-separated, one entry per line, header lines start with `#`:

```
utc_timestamp    student_ids (ABC123456 or ABC123456+DEF654321)    run_tag    variant    client_ip
```

Filter grading entries with `grep -P '\tgrading-k[123]\t' ledger.tsv`.

## Commands

```
docker build -t harness-sandbox tools/sandbox/
python3 tools/runner.py --project project.json --create-slots
python3 tools/ledger_server.py --resource resource/ --ledger ledger.tsv --nonce <NONCE> --port 8080 \
        --base-url http://host.docker.internal:8080
python3 tools/prescan.py submissions/ --allow host.docker.internal
python3 tools/runner.py --project project.json --submissions submissions/ --status status.csv --out runs/
python3 tools/grade.py --project project.json --runs runs/ --status status.csv --written written.csv \
        --milestone milestone.csv > gradebook.csv
```

## Things to verify during the calibration run

These are documented behaviours of the tools involved that this repository has not exercised end to end:

- The OpenCode configuration shape written by `runner.py` (`provider.ollama` via `@ai-sdk/openai-compatible`, `permission` block) against the current OpenCode docs.
- That `opencode run --format json` exits non-zero on failure and finishes without a TTY.
- That the Ollama Modelfile `PARAMETER seed` is honoured by the `/v1` endpoint OpenCode uses.
- That `host.docker.internal` resolves on the grading machine (Linux needs the `--add-host` flag the runner already passes).

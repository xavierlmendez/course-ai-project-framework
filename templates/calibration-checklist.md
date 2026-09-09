# Calibration checklist

Run before release. Do not release until every box in your project's path is ticked.
Sections are in execution order: Setup, then the gate for your type, then Sanity, Record, Lock.

## Setup (both types)

- [ ] Reference harness installed exactly as the student install guide says. Model tag pinned in `project.json`, and `num_ctx` set (32768; the agent loop's tool schemas do not fit Ollama's 4096 default).
- [ ] **The model emits structured tool calls** through the harness's provider path: five attempts against the model server with one tool definition, five `tool_calls` replies. This is the sixth harness criterion (`framework.md` §5) and it is the cheapest box on this page — a model that fails it produces no entry point at all, and every regeneration would be scored as the student's failure. Do not infer it from `ollama show`'s `Capabilities: … tools`, which describes the chat template.
      `MODEL=$(python3 -c 'import json;print(json.load(open("project.json"))["base_model"])'); bash scripts/cpu_verify.sh   # the tooltest function; expect 5/5 at num_ctx 32768`
- [ ] The harness's provider timeouts exceed `regeneration_timeout_s`. The runner writes OpenCode's `headerTimeout` and `chunkTimeout` from it; confirm they are in the generated `opencode.json` and that no slot dies at exactly 300 s.
- [ ] Ledger server running and reachable from inside the sandbox; the published resource served from it with the nonce visible.
- [ ] **On a Linux grading box: install and open up the model server, then build and test the sandbox.** Four commands, in this order; Docker Desktop on macOS needs only the pull and the build.
      `curl -fsSL https://ollama.com/install.sh | sh`
      `sudo mkdir -p /etc/systemd/system/ollama.service.d && printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf && sudo systemctl daemon-reload && sudo systemctl restart ollama`
      `ollama pull qwen3:14b   # or the project's base_model`
      `docker build -t harness-sandbox tools/sandbox/ && python3 -m unittest tests.test_sandbox   # 11 tests, about 25 s`
- [ ] **On Linux: the model server is reachable from inside the sandbox.** Ollama binds 127.0.0.1 by default, so the container cannot reach `host.docker.internal:11434` even though a host-side dial says ok, and every slot then fails after about a minute with OpenCode's "Cannot connect to API". The `OLLAMA_HOST=0.0.0.0` override above is the fix; on Docker Desktop it is automatic. `--verify-slots` now also probes the model server from inside the sandbox and names this fix if that probe fails, and every sandboxed batch does the same.
      `docker run --rm --add-host host.docker.internal:host-gateway --entrypoint curl harness-sandbox -s -m 5 http://host.docker.internal:11434/api/tags`
- [ ] Hidden tests in `tests/hidden/<category>/`, weights in `project.json`, twist categories summing to half the hidden weight. Variant projects generate them instead: see **Per-student variants**.
- [ ] A canonical solution exists in `canonical/` (the textbook problem, twist ignored). It is what proves the twist is load-bearing.

## Setup (Type B only, in this order)

Type A needs no seeds and no slot models: its gate runs no harness.

- [ ] Create the seeds. Not committed, not shared with TAs until grading day.
      `python3 -c 'import json,secrets;json.dump({"seeds":[secrets.randbelow(900000)+100000 for _ in range(3)]},open("seeds.secret.json","w"))'`
- [ ] Create the per-slot model variants (writes a Modelfile with each slot's temperature and seed, then runs `ollama create`).
      `python3 tools/runner.py --project project.json --create-slots`
- [ ] Confirm the schedule reaches the model.
      `python3 tools/runner.py --project project.json --verify-slots`

## Type A gate (deterministic, decision 21)

No harness run. The gate is that the hidden suite separates a correct solution from a twist-ignoring one.

- [ ] Reference solution passes **every** hidden test, including the graduate category.
      `python3 tools/run_tests.py --solution reference/solution --tests tests/hidden`
- [ ] Canonical solution fails the twist categories.
      `python3 tools/run_tests.py --solution canonical --tests tests/hidden`
- [ ] Per-case timings recorded from the reference run; they set `test_timeout_s` (see **Record**).
      `python3 tools/run_tests.py --solution reference/solution --tests tests/hidden --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(max(c["wall_s"] for v in d["categories"].values() for c in v["cases"]))'`

## Type B gate

The reference specification is written by the professor within the same caps students have (1,500 words) and contains the ledger sign instruction.

- [ ] Stage a calibration directory holding **only** the specification.
      `mkdir -p calibration/spec-only && cp reference/SPEC.md calibration/spec-only/`
- [ ] Run the calibration from that directory, never from `reference/`. `reference/` also holds `reference/solution/`, and a gate that hands the harness the professor's own answer measures nothing.
      `python3 tools/runner.py --project project.json --submission calibration/spec-only --out runs-calibration --run-tag calibration`
- [ ] **At least one of the K runs passes every hidden test, including the graduate category.** If not: simplify the twist or clarify the resource. Do not weaken the tests to fit the model.
- [ ] Ledger shows K entries with run tags `calibration-k1..k3` and the correct nonce.
- [ ] **The ledger's run-tag column reads the calibration tag, not `practice`.** The runner passes `RUN_TAG` into the harness environment and the resource page's ledger line reads `run_tag=${RUN_TAG:-practice}`, so a row tagged `practice` after a calibration run means the harness's shell never saw `RUN_TAG` — seen once on a GPU run, cause not yet established, so check it every time rather than assuming it is fixed. It matters because the TA's Type B ledger check (runbook Day 1 evening step 5) greps the run-tag column for `grading-k<N>`: a batch whose entries all say `practice` reports every student as having no ledger entry. If you see it, report it to the framework maintainers with the run record.
      `awk -F'\t' '{print $3}' <the ledger> | sort | uniq -c`
- [ ] Wall-clock time of the slowest passing run recorded; it sets `regeneration_timeout_s` (see **Record**).

## Per-student variants (variant projects only)

Variant projects ship no `tests/hidden/`: the generator writes one hidden suite per variant. Gate on at least two variants, not one.

- [ ] Generate variant 1's hidden tests.
      `python3 tests/gen_hidden.py --variant <V1> --out /tmp/hidden-V1`
- [ ] Generate variant 2's hidden tests.
      `python3 tests/gen_hidden.py --variant <V2> --out /tmp/hidden-V2`
- [ ] Reference passes every test on variant 1.
      `python3 tools/run_tests.py --solution reference/solution --tests /tmp/hidden-V1`
- [ ] Reference passes every test on variant 2.
      `python3 tools/run_tests.py --solution reference/solution --tests /tmp/hidden-V2`
- [ ] Canonical fails the twist categories on variant 1.
      `python3 tools/run_tests.py --solution canonical --tests /tmp/hidden-V1`
- [ ] Canonical fails the twist categories on variant 2.
      `python3 tools/run_tests.py --solution canonical --tests /tmp/hidden-V2`
- [ ] Every `student_id` in `variants.csv` matches a submission directory name exactly: a single ID, or `A+B` / `A-B` for a pair. The tools accept either pair form, but the roster key and the directory name must be the same string.
      `python3 -c 'import csv,os;r={x["student_id"].strip() for x in csv.DictReader(open("variants.csv"))};d=set(os.listdir("submissions"));print("roster only:",sorted(r-d));print("dirs only:",sorted(d-r))'`

## Sanity

- [ ] Deterministic checks show **zero FAIL rows** for the project being calibrated.
      `python3 scripts/review_checks.py --no-network --out checks.md`
- [ ] An **empty** specification ("write solve.py") scores near zero. Type B only.
      `mkdir -p calibration/empty && printf 'Write solve.py.\n' > calibration/empty/SPEC.md && python3 tools/runner.py --project project.json --submission calibration/empty --out runs-calibration --run-tag calibration`
- [ ] The public suite passes against the reference solution from the milestone command students will use.
      `python3 tools/run_tests.py --solution reference/solution --tests tests/public`

## Record

Write these into `project.json` before release.

- [ ] `regeneration_timeout_s` = **2 ×** the measured regeneration wall-clock time of the slowest passing calibration run. Type B only.
- [ ] `test_timeout_s` = **at least 3 ×** the slowest per-case time measured in the gate above.
- [ ] The measured numbers themselves, with the date and the machine, in the project's notes; the runbook's time budget comes from them, not from a guess.

## Lock

- [ ] `seeds.secret.json` still uncommitted and unshared; TAs get it on grading day.
- [ ] Published resource frozen: no edits between release and the end of the appeals window. If an edit is unavoidable, announce it and note the date in the ledger file header.
- [ ] The reference specification (Type B) or the reference solution (Type A) is filed as the appeals answer key.
- [ ] The calibration staging directories (`calibration/`, `runs-calibration/`) deleted or gitignored.

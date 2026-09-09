# CS 6XX Project 3: Bencode-L encoder (Specification Project)

## 1. The task

Write a specification that makes the reference harness produce `solve.py`, an encoder from JSON values to **Bencode-L**, a variant of BitTorrent's bencoding. The base format is documented externally; the variant rules are on the course resource page. Your specification must get the harness to read both.

## 2. The published resource and the ledger

The full task, including the rules that differ from standard bencoding, is at:

**http://localhost:8082/** (from inside the grading sandbox: `http://host.docker.internal:8082/`). 8082 is this project's `resource_port`.

To practise at home, start that server yourself from the root of the course repository:

```
python3 tools/ledger_server.py --project examples/03-serialization-type-b-research/project.json --allow-in-repo
```

It listens on the project's `resource_port`, prints the nonce it is serving, and writes `examples/03-serialization-type-b-research/ledger.tsv`. `--allow-in-repo` is needed only because that path is inside a checkout: the server refuses by default so that a real ledger of student IDs is never one `git add .` from being committed, and a practice ledger is throwaway. That is your own ledger; the graded one is the course server your instructor announces.

It links a snapshot of the external specification. Use the snapshot; the live page is not reachable from the sandbox.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your specification must tell the harness to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12 or later, standard library only |
| Entry point | `solve.py` in the root of the generated solution |
| Input | one JSON object on stdin: `{"value": V}` |
| Output | one JSON object on stdout: `{"hex": H}`, nothing else |
| Time limit | 10 seconds per test case |

Worked example:

```
$ echo '{"value": ["spam", "eggs"]}' | python3 solve.py
{"hex": "6c343a7370616d343a6567677365"}
```

## 4. Tests

Public tests are in `examples/03-serialization-type-b-research/tests/public/`. From the root of the course repository:

```
python3 tools/run_tests.py --solution <your dir> \
  --tests examples/03-serialization-type-b-research/tests/public --entry solve.py --timeout 10
```

**Two names used throughout this handout.** `<your dir>` is the directory holding your submission files, for example `mywork/`; use its path wherever `<your dir>` appears. `runs/` is where the runner writes: it creates `runs/<your dir's name>/` beside where you run the command, and every record and working directory named below lives inside it.

`run_tests.py` prints a summary either way; `--json` prints **only** the JSON summary instead of the human-readable one, for feeding into another program.

Hidden categories:

| Category | Cases | Weight | Graduate only |
|---|---|---|---|
| basic_scalars | 8 | 1 | no |
| lists | 6 | 1 | no |
| dicts | 6 | 1 | no |
| twist_length_prefix | 8 | 1 | no |
| twist_key_order | 7 | 1 | no |
| twist_bool_null | 8 | 1 | no |
| grad_deep_nesting | 5 | 1 | yes |

## 5. The reference harness

Your grade comes from **OpenCode on Ollama with the model named in `examples/03-serialization-type-b-research/project.json`** (the `base_model` key), run by the TAs. Develop with whatever you like; optimizing for another tool is pointless.

Install guide: the [student primer](../../templates/student-primer.md). Read it before the milestone.

**If your machine cannot run the model.** Running Ollama locally needs no edit: the `ollama_host` shipped in `project.json` is the grading container's view of the model server, and a practice run (which uses no sandbox) substitutes `127.0.0.1` for it automatically. To use the course Ollama server your instructor announces, add `"ollama_host_local"` to **your own copy** of `project.json`, set to the server URL as your machine reaches it. Leave `ollama_host` alone — it describes the grading run. Exporting `OLLAMA_HOST` does not redirect OpenCode.

Run your specification the way the TAs will, from the root of the course repository:

```
python3 tools/runner.py --project examples/03-serialization-type-b-research/project.json \
  --submission <your dir> --practice
```

`--practice` needs nothing you do not have: it runs outside the grading sandbox, tags the run `practice`, runs the **public** suite, writes `seeds.practice.json` with three seeds of your own (the grading seeds are secret until grades are out), and creates the pinned per-temperature models if your Ollama has none. The TA run differs only in the seeds and the sandbox.

## 6. What to submit

| File | Cap |
|---|---|
| `SPEC.md` | 1,500 words including any supporting files |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded, see §8 |

Do **not** submit generated code. It is not graded.

## 7. Milestone (end of week 1, 10%)

Your specification passes the public suite through the reference harness. Do the `--practice` run in §5 first — a real run, not a dry run — then build the record from what it wrote:

```
python3 tools/milestone.py record \
  --project examples/03-serialization-type-b-research/project.json \
  --solution runs/<your dir>/practice-k1-work \
  --regeneration runs/<your dir>/practice-k1.json \
  --student-id <your student ID> --out milestone.json
```

This is a Type B project, so `--regeneration` is **required** and `--solution` must be that regeneration's own working directory — the `-work` directory beside the record. A record built from anything else, including a dry-run record (named `*.dry.json`), is rejected.

Submit `milestone.json`. Auto-graded pass/fail.

## 8. Grading

| Component | Weight |
|---|---|
| Milestone | 10 |
| Hidden tests (best of 3 regenerations) | 70, twist categories carry 35 |
| Written component | 20 |

**Regeneration.** The TAs run your `SPEC.md` through the reference harness three times, at temperatures 0.2, 0.6, and 1.0, with a fixed seed per temperature that is secret until grades are released. Your hidden-test score is the best of the three. A run that exceeds 20 minutes or produces a solution that does not start scores zero for that run.

**Written component** (`WRITTEN.md`, one page), scored 0–3 on each of:

- *Accuracy*: explain how you developed the specification; does it match what `SPEC.md` says?
- *Twist specificity*: which lines of your specification handle the twist, and why those?
- *Candor*: name one thing the harness got wrong and what you changed.
- *Graduate only, Prediction*: which hidden categories will your specification fail, and why?

## 9. What is not graded

Harness choice, model choice, how the page was fetched, the code the harness produced during your development, the number of times you regenerated, and the process note.

## 10. Integrity

Specifications are text and are treated like code: they are submitted to MOSS, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. Pairs submit one directory and both sign the ledger. The twist changes every semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

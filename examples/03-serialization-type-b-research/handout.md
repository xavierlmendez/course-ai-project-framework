# CS 6XX Project 3: Bencode-L encoder (Specification Project)

## 1. The task

Write a specification that makes the reference harness produce `solve.py`, an encoder from JSON values to **Bencode-L**, a variant of BitTorrent's bencoding. The base format is documented externally; the variant rules are on the course resource page. Your specification must get the harness to read both.

## 2. The published resource and the ledger

The full task, including the rules that differ from standard bencoding, is at:

**http://localhost:8080/** (from inside the grading sandbox: `http://host.docker.internal:8080/`)

It links a snapshot of the external specification. Use the snapshot; the live page is not reachable from the sandbox.

Your harness must fetch that page. It contains a nonce and a ledger instruction.

**Your specification must tell the agent to sign the course ledger with your student ID (and your partner's, if any) and the nonce from the page.** A specification that does not produce a ledger entry has not specified the task.

We cannot tell whether the page was fetched by your harness or by you with `curl`, and we do not try. The ledger entry is what counts.

## 3. Interface contract

| | |
|---|---|
| Language | Python 3.12, standard library only |
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

Public tests are in `tests/public/`. Run them with:

```
python3 tools/run_tests.py --solution <dir> --tests tests/public
```

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

Your grade comes from **OpenCode with model `qwen2.5-coder:14b`** on Ollama, run by the TAs. Develop with whatever you like; optimizing for another tool is pointless.

Install guide: see `tools/README.md` in the course repository. A shared Ollama server is at `http://ollama.cs.example.edu:11434` for anyone whose machine cannot run the model.

Run your specification the way the TAs will:

```
python3 tools/runner.py --project project.json --submission <dir> --run-tag practice --tests tests/public --no-sandbox
```

(The TA run uses secret seeds and the sandbox; yours uses the same temperatures with seeds of your choosing.)

## 6. What to submit

| File | Cap |
|---|---|
| `SPEC.md` | 1,500 words including any supporting files |
| `PROCESS.md` | 1 page, 600 words; required, not graded |
| `WRITTEN.md` | 1 page, 600 words; graded, see §8 |

Do **not** submit generated code. It is not graded.

## 7. Milestone (end of week 1, 10%)

Your specification passes the public suite through the reference harness. Produce the record with `tools/milestone.py record` (its help shows the Type B path, which points at the working directory your practice run produced) and submit it. Auto-graded pass/fail.

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

Specifications are text and are treated like code: they are submitted to {{SIMILARITY_TOOL}}, the institution's similarity checker, and anything it flags goes to the professor under the standard misconduct process. Pairs submit one directory and both sign the ledger. The twist changes every semester.

## 11. Appeals

If you believe a regeneration was unlucky, you may request one additional run at temperature 0.6, granted only if you demonstrate the specification passes the public suite on the reference harness.

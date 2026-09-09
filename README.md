# AI-Assisted Course Project Framework

A reusable way to give a course project in which students direct an AI harness with internet access, without paid subscriptions, graded by TAs reproducibly and fairly. Abstracted from course content: the four examples cover games, search, data representation, and scheduling, and none of the machinery cares which.

**Start with [framework.md](./framework.md).** It is the professor-facing document; everything else supports it. A shareable rendered version is published at https://claude.ai/code/artifact/7aa021bf-eae9-4752-aa3c-a2337e95d86d (private until shared).

## Map

| Path | What |
|---|---|
| [framework.md](./framework.md) | The design, the reasoning, the professor's workflow, the options menu |
| [CONTEXT.md](./CONTEXT.md) | Glossary. Every document uses these terms exactly |
| [templates/](./templates/) | Handout (Type A, Type B), [student primer](./templates/student-primer.md), rubric, twist checklist, calibration checklist, TA runbook, rotation checklist, process-note prompt |
| [tools/](./tools/) | `runner.py`, `run_tests.py`, `milestone.py`, `grade.py`, `grade_all.py`, `combine_parts.py`, `prescan.py`, `ledger_server.py`, `sandbox/`. Python standard library + Docker + Ollama. [tools/README.md](./tools/README.md) has the `project.json` schema and the command for each tool |
| [examples/01-morris-type-b](./examples/01-morris-type-b/) | The professor's actual Spring 2026 Morris-variant project recast: Type B, eight programs in one directory each (45/35/10/10 across four parts, split evenly between each part's Opening and Game program), file-argument CLI contract, equivalence policies per category |
| [examples/02-astar-type-a](./examples/02-astar-type-a/) | Type A, published resource, A* with a published movement twist |
| [examples/03-serialization-type-b-research](./examples/03-serialization-type-b-research/) | Type B, research-pointer variant (external spec + twist, snapshotted) |
| [examples/04-scheduling-type-a-variants](./examples/04-scheduling-type-a-variants/) | Type A, per-student variant parameters with generated hidden tests |
| [docs/grill/](./docs/grill/) | The six-round design interview that produced every decision, plus the round-07 amendment that corrected the account of the previous project; `round-06.md` is the one-page summary |
| [docs/adr/](./docs/adr/) | The three decisions that were hard to reverse |
| [docs/research/](./docs/research/) | Free-harness survey, 2026-09-08; the previous project's rubric and what it left open |
| [docs/DECISIONS.md](./docs/DECISIONS.md) | The decision log; the three hardest to reverse also have full ADRs |
| [docs/BACKLOG.md](./docs/BACKLOG.md) | Deferred work; every `TODO(BL-nn)` in code resolves here |
| [docs/review/](./docs/review/) | The 2026-09-08 review: findings, the fix plan and its phases, deterministic checks, evidence |
| [CLAUDE.md](./CLAUDE.md) | Agent guide: read order, hard rules, commands |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Branches, slices, tests, commit format |
| [tests/](./tests/) · [scripts/](./scripts/) | The standard-library test suite; the rehearsal, the deterministic checks, and the `cpu_verify.sh` / `gpu_verify.sh` harness probes |

## Test and check

Everything here is Python 3 standard library; there is nothing to install.

```
python3 -m unittest discover -s tests -p "test_[a-r]*.py"   # fast suite: no Docker, no network
python3 scripts/rehearsal.py                                # a fixture cohort end to end
python3 scripts/review_checks.py --no-network --out /tmp/checks.md
```

The sandbox tests need a built image and run separately:

```
docker build -t harness-sandbox tools/sandbox/
python3 -m unittest tests.test_sandbox
```

`review_checks.py` must report **zero FAIL rows**, and CI fails on any of them. (It reported FAIL rows
for example 01's stub parts until backlog entry BL-01 landed; there are no stubs left.)

## Ten-minute tour

1. Read framework.md §1 and §2 (the design and why the prompt itself is not graded).
2. Open `examples/02-astar-type-a/resource/index.md` to see a published resource with a twist, a nonce, and a ledger instruction.
3. Run the reference solution against the hidden tests:
   ```
   python3 tools/run_tests.py --solution examples/02-astar-type-a/reference/solution --tests examples/02-astar-type-a/tests/hidden
   ```
4. Run the canonical (twist-ignored) solution the same way and watch the twist categories fail.
5. Read `templates/ta-runbook.md` to see the grading week.

## What has been verified here and what has not

Verified on this machine (macOS, Python 3.14, Docker Desktop):

- `run_tests.py` (both the stdin/stdout and the file-argument contracts, the latter against Xavier's real reference program), `grade.py`, `combine_parts.py`, `prescan.py`, `ledger_server.py` against fixtures and the four examples.
- All four examples: reference solutions pass every hidden test; canonical solutions score visibly low on twist categories; sample student submissions pre-scan clean.
- The sandbox image builds; inside it, tests run as an unprivileged user, the outbound firewall blocks an outside host and admits the resource host, and a ledger signature from inside the container reaches the ledger file.
- The runner's sandboxed Type A path on examples 02 and 04 (including per-variant test generation); Type B dry runs on examples 01 and 03.

Not verified: an actual regeneration through OpenCode against an Ollama `qwen3:14b` model on the grading machine. The calibration checklist covers exactly this, and `tools/README.md` lists the four behaviours to confirm. The model itself was measured on 2026-09-09 and does emit structured tool calls (5/5 at `num_ctx` 32768), which is why it replaced `qwen2.5`-coder — see `docs/review/evidence/harness-tool-calling.md` and D-006.

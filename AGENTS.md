<!-- from engineering-standards @ 1b9616e (CLAUDE.template.md), adapted for a stdlib-only repo -->
# course-ai-project-framework — Agent Guide

This file follows the cross-tool `AGENTS.md` convention: OpenCode, Codex, Copilot, Cursor and
Gemini CLI read it directly, and `CLAUDE.md` imports it for Claude Code. Human readers start at
`README.md`.

A reusable design for a course project in which students direct an AI harness with internet access,
graded by TAs reproducibly and fairly without paid subscriptions. It is a documentation-and-tools
repository, not an application: `framework.md` is the professor-facing document and everything else
supports it. The single most important constraint is **Python standard library only** — the tools must
run on a bare lab machine with no package manager (decision 20).

## Read before working (in order, only what the task needs)

1. `docs/review/fix-plan.md` — the active plan: phases, slices, and the 24 settled decisions
2. `docs/DECISIONS.md` — decisions with lasting consequences; don't re-litigate, append new ones
3. `README.md` — layout, run, test, and check commands
4. `docs/BACKLOG.md` — every `TODO(BL-nn)` in code resolves here
5. `CONTEXT.md` — the glossary; every document uses these terms exactly

## Hard rules

- **Standard library only.** No third-party Python packages, no `uv`, no `pytest`, no `ruff`.
  Docker and Ollama are external tools the harness uses, not import-time dependencies (decision 20).
- **Every tool change ships with a test** in the same slice, and a fix ships the test that fails
  before it (`CONTRIBUTING.md`). Tests are deterministic: no network, no wall clock, no unseeded
  randomness.
- **`seeds.secret.json` is never committed.** It is gitignored; `scripts/review_checks.py` asserts
  no seed file is tracked. Never print a seed in tool output before grades are released.
- **Ledger files are never committed.** `ledger.tsv` and `course-ledger.tsv` hold student IDs and
  client addresses; both are gitignored and `ledger_server.py` refuses to write inside a repository.
- **`# TODO(BL-nn): …` is the only accepted TODO form.** Unstarted work goes to `docs/BACKLOG.md`,
  not to empty modules or commented-out designs.
- **`main` is always green.** Every slice is one branch and one PR (decision 14).
- Where a document states the intended policy the tool changes; where the tool is right the document
  changes. No settled decision is reopened (decision 1).

## Commands

Fast suite (no Docker, no Ollama, no network):

```
python3 -m unittest discover -s tests -p "test_[a-r]*.py"
```

End-to-end rehearsal of a fixture cohort through the grading tools:

```
python3 scripts/rehearsal.py
```

Deterministic repository checks (examples, weights, links, standards files):

```
python3 scripts/review_checks.py --no-network --out /tmp/checks.md
```

Sandbox image and its tests (needs Docker; slow, excluded from the fast suite):

```
docker build -t harness-sandbox tools/sandbox/
python3 -m unittest tests.test_sandbox
```

## Conventions

- PEP 8 names: `snake_case` modules and functions, `CapWords` classes, `UPPER_CASE` constants.
- Commits: `<type>(<scope>): <imperative summary>` per Conventional Commits; one branch per slice,
  named `<type>/<slug>`.
- Dates ISO 8601. Line length 100 in code; prose documents wrap at 100 where practical.
- After any decision with lasting consequences, append to `docs/DECISIONS.md` in the same PR, and add
  an ADR under `docs/adr/` when the decision is hard to reverse.
- Findings from the 2026-09-08 review are numbered `F-nn` in `docs/review/findings.md`; a slice that
  closes one names it in the commit message.

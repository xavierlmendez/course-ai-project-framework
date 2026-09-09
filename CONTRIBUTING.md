<!-- from engineering-standards @ 1b9616e -->
# Contributing

These rules keep `main` clean without relying on memory. CI and pre-commit enforce them.

## Branches and merging

- `main` is protected: PR required, CI status check required, force-push disallowed.
  (GitHub branch protection / rulesets — see SOURCES.)
- Branch names: `<type>/<slug>` with type ∈ `feat fix refactor docs chore ci test`.
- Squash-merge. Delete the branch after merge. A branch older than 30 days is merged or deleted.

## Slices

A PR is one *slice*: a vertical slice of functionality — one end-to-end piece that a reader can run,
test and judge on its own, with a one-sentence title. It cuts through every layer the piece needs
(contract, implementation, tests, records) rather than delivering one layer of several pieces.
Size follows from the functionality, never the other way round: a slice is as large as the smallest
end-to-end piece and no larger. "Split larger work before opening" means finding a smaller
end-to-end piece, never shipping a layer without the rest. Format-only and rename-only changes are
their own slices and are listed in `.git-blame-ignore-revs`.

## No unstarted code on `main`

Empty modules, `pass`-only placeholders, and commented-out designs do not merge. Record the intent
in `docs/BACKLOG.md` (with the design sketch if one exists) and reference it from code as
`# TODO(BL-nn): …`. Ruff `TD` rules enforce the shape; CI greps for a TODO without an id.

## Tests

Every feature or bug fix ships with a test in the same PR. Tests are deterministic: no network,
no wall clock, no unseeded randomness. A bug fix adds the test that would have caught it first.
The full standard is `.claude/agents/testing-agent.md`.

## Behavioural baseline before a refactor

Before restructuring code that trains or transforms data, add a test that runs the real pipeline on a
small, seeded configuration and snapshots its outputs (metrics, or shape + columns + content hash of
frames). Commit the snapshot. Every refactor slice must leave it byte-identical; regenerate it only in a
PR that says why the numbers are *supposed* to change. When deleting the code the snapshot was taken
from, capture its fingerprints first and test against those — the guarantee outlives the oracle.
(Back-ported from botMaker, 2026-08-29: the baseline found three latent bugs before any refactor began.)

## Records

- A decision with lasting consequences → `docs/DECISIONS.md` entry in the same PR.
- A technique implemented by hand (learning repos) → `docs/LEARNING_LOG.md` entry in the same PR.

## Commits

Conventional Commits: `<type>(<scope>): <imperative summary>`; body says *why* when non-obvious;
`BREAKING CHANGE:` footer or `!` when applicable. Types: `feat fix docs refactor test chore ci build perf style`.

## Definition of done

CI green · tests added · decision/learning/backlog entries updated · no TODO without an id ·
branch deleted after merge.

## Back-porting

When a config or rule here turns out wrong in a repo, fix it there, then open a PR against
`engineering-standards` with the same change and a one-line reason.

---

## This repo

Two adaptations, and nothing else changes:

- **Standard library only.** There is no `uv`, no `ruff`, no `pyproject.toml`, and no lockfile: the
  tools must run on a bare lab machine (decision 20 in `docs/review/fix-plan.md`). Where the rules
  above name a ruff rule, the equivalent here is the CI grep and review.
- **`unittest`, not `pytest`.** The fast suite is
  `python3 -m unittest discover -s tests -p "test_[a-r]*.py"`; `tests/test_sandbox.py` needs a built
  Docker image and runs separately. Fixtures are built in a temporary directory by `tests/helpers.py`
  rather than by fixture plugins. The behavioural-baseline rule applies to the grading arithmetic:
  `scripts/rehearsal.py` is the snapshot.

Records here are `docs/DECISIONS.md` plus an ADR under `docs/adr/` when a decision is hard to
reverse, and `docs/BACKLOG.md`; there is no `docs/LEARNING_LOG.md`.

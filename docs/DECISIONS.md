<!-- from engineering-standards @ 1b9616e (templates/DECISIONS.md) -->
# Decisions

Append-only log of decisions with lasting consequences (ADR style). Don't edit old entries; supersede
them. Newest at the bottom. The three decisions that were hardest to reverse also have full ADRs in
[`adr/`](./adr/); this log is the index and the one-paragraph summary, the ADR carries the
alternatives and the reasoning. The 24 numbered plan decisions taken during the 2026-09-08 review live
in [`review/fix-plan.md`](./review/fix-plan.md) §2 and are referenced from here as "decision *n*".

## D-001 — The course owns the execution; the reference harness is a local, pinned model · 2026-09-08 · status: accepted

**Context.** The previous project graded code students generated with whatever model they had, which
gave uncontrolled temperature, per-student best-of-N, and an advantage to paid accounts; cloud free
tiers reroute models mid-session and expose no seed, so appeals could not be rerun.
**Decision.** Grades come only from executions the course performs, on a reference harness chosen
under five published criteria; this year's instance is OpenCode on Ollama with `qwen2.5-coder:14b`,
pinned per slot by Modelfile `temperature` and `seed`.
**Consequences.** Regenerations are reproducible and appeals rerunnable; the graded model is weaker
than frontier models so every task must be calibrated against it; hardware, not subscriptions,
becomes the equity question. Full record: [`adr/0001-course-owns-execution.md`](./adr/0001-course-owns-execution.md).

## D-002 — Best-of-K at a fixed temperature schedule with secret per-slot seeds · 2026-09-08 · status: accepted

**Context.** A specification run through a model is nondeterministic: one run is a lottery and
unlimited runs reward effort and luck rather than the specification.
**Decision.** K=3 regenerations at temperatures 0.2, 0.6, 1.0, identical for every student, each slot
with a fixed seed kept secret until grades are released and published afterward with the hidden tests;
the hidden-test score is the best of the three.
**Consequences.** Every specification faced the same three conditions, which is the fairness argument
in one sentence; median-of-K and published seeds were rejected. Full record:
[`adr/0002-best-of-k-fixed-schedule-secret-seeds.md`](./adr/0002-best-of-k-fixed-schedule-secret-seeds.md).

## D-003 — The specification, not the runner, carries the ledger sign instruction · 2026-09-08 · status: accepted

**Context.** The published resource tells the harness to sign the ledger with the student's ID; in
Type B the TA runs the regeneration, so someone must supply that instruction, and injecting it for
every student would make the ledger measure only the runner.
**Decision.** The student's specification is responsible for telling the harness to fetch the resource
and sign the ledger; the runner adds only a run tag through the environment (`RUN_TAG`).
**Consequences.** The specification remains the whole graded object; a specification that omits the
instruction produces no ledger entry (informational for Type B, a gate for Type A), so the handout
must state the requirement in one bold line. Full record:
[`adr/0003-specification-carries-the-ledger-instruction.md`](./adr/0003-specification-carries-the-ledger-instruction.md).

## D-004 — The reference model is selected by a measured tool-calling test, not by a capability flag · 2026-09-08 · status: accepted

**Context.** The harness survey ([`research/harness-survey-2026-09-08.md`](./research/harness-survey-2026-09-08.md))
found that documented capability tables do not predict behaviour: a harness advertising a web-fetch
tool may not call it under a given model, and the parameters a harness claims to support may never
reach the model — measured on 2026-09-08, OpenCode 1.18.29 sends no temperature field at all, so the
Modelfile governs ([`review/evidence/f65-temperature-path.md`](./review/evidence/f65-temperature-path.md),
decision 24).
**Decision.** A model or harness is admitted to the reference stack only after a measured test on the
grading path: the harness is run against the published resource and the ledger entry, the effective
parameters are read back from the model before grading, and a mismatch fails loudly. Documented
capability flags are treated as a shortlist, never as evidence.
**Consequences.** Adopting a new harness or model costs a measurement run rather than a documentation
read, and the runner carries a self-check it would not otherwise need; in exchange, the failure mode
where a whole cohort is graded at the wrong temperature cannot ship silently.

## D-005 — Grading arithmetic and sandbox controls are guarded by tests that fail before the fix · 2026-09-08 · status: accepted

**Context.** The verification numbers recorded on 2026-09-08 could not be reproduced: there were no
tests and no fixtures, so a changed category weight or written scaling would have produced wrong
grades with nothing failing (F-50). Two Phase 2 controls also passed at first for the wrong reason.
**Decision.** Every grading-arithmetic and sandbox-control fix ships in the same slice as a
standard-library `unittest` test that fails against the code as it stood, on fixtures built in a
temporary directory; a test that cannot be made to fail is rewritten until it can.
**Consequences.** Phase 1 landed 55 tests, 28 of which failed beforehand; Phase 2 landed 11 sandbox
tests, six of which failed beforehand and two of which were rewritten after they passed vacuously.
The suite is slower to write than assertions after the fact, and the Docker-dependent sandbox tests
are excluded from the fast suite, but the recorded numbers are now reproducible on demand.

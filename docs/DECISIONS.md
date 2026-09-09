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
under published criteria; this year's instance is OpenCode on Ollama with the model named in
`project.json`, pinned per slot by Modelfile `temperature` and `seed`. (The model tag named here on
2026-09-08 was replaced on 2026-09-09; see D-006. The criteria were five; D-006 adds a sixth.)
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

## D-006 — The reference model is `qwen3:14b`, and a sixth harness criterion is structured tool calls · 2026-09-09 · status: accepted

**Context.** The reference instance named in D-001 — the Qwen 2.5 coder model at 14B — met all five published
criteria and still could not be graded with: measured on 2026-09-09 through Ollama's `/api/chat` and
`/v1/chat/completions`, it returned its tool call as ordinary assistant text on **0 of 5** attempts at
`num_ctx` 4096 and **0 of 5** at 32768, so OpenCode's agent loop never began, the working directory
held no entry point, and the runner recorded a complete run with a hidden score of zero. A whole
cohort would have been graded on the machine's failure. `qwen3:14b`, on the same box, the same Ollama
0.33.3 and the same probe, returned a real `tool_calls` entry on **5 of 5** attempts at 32768.
Evidence: [`review/evidence/harness-tool-calling.md`](./review/evidence/harness-tool-calling.md).
**Decision.** The reference harness instance is **OpenCode 1.18.29 + Ollama + `qwen3:14b`**, and
`framework.md` §5 gains a **sixth criterion**: the model must emit structured tool calls through the
harness's provider path, verified before the semester by a five-attempt probe
(`scripts/cpu_verify.sh`, the `tooltest` function) rather than assumed from Ollama's capability flag,
which describes the chat template and not the model. Two supporting changes ship with it: every
`project.json` carries `"num_ctx": 32768`, because the agent loop's tool schemas do not fit Ollama's
4096 default; and the runner writes OpenCode's `headerTimeout` and `chunkTimeout` as
`regeneration_timeout_s × 1000`, because OpenCode 1.18.29 otherwise aborts any provider request whose
headers or next chunk take longer than 300 s — which a 14B model on a CPU box exceeds before its
first token, and which would have been mis-scored as the student's failure rather than an
environment error.
**Consequences.** The calibration gate acquires a cheap pre-check that fails in seconds instead of a
cohort. Everything downstream of the model tag is unaffected: the pinning, the seeds, the temperature
schedule, the sandbox, the grading arithmetic and the ledger are all independent of which model is
chosen. The cost is memory: at `num_ctx` 32768 the 14B model occupies about 15 GB rather than 9, so a
16 GB laptop swaps and the shared course server becomes the recommended route for students who do
not have the headroom. D-001's model tag is superseded; its rule is not.

## D-007 — `qwen3` thinking mode is left at Ollama's default · 2026-09-09 · status: open

**Context.** `qwen3:14b` reports `completion, tools, thinking`: it can emit a reasoning block before
its answer, and Ollama exposes a `think` parameter to turn that off. The tool-calling probe was run
with `"think": false`; the reference stack does not set it, so regenerations run at whatever default
Ollama applies to the tag. Thinking plausibly improves specification-following — the property the
whole project measures — and just as plausibly doubles the wall clock of every regeneration on a CPU
box, which moves `regeneration_timeout_s`, the calibration numbers and the grading-day budget in the
TA runbook.
**Decision.** Not taken. The professor decides before the semester, on measurement: run the
calibration gate both ways and compare pass rate against wall clock. Until then the default stands
and is recorded here so that a run's behaviour is not silently attributed to the model tag alone.
**Consequences.** Whichever way it goes, the choice must be pinned before the seeds are created and
must not change mid-cohort: the reproducibility promise in §6 covers the weights, the seed, the
temperature and the wrapper prompt, and a thinking flag changed between slots would break it.

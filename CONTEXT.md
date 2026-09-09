# AI-Assisted Course Project Framework

A reusable framework for course projects in which students direct an AI harness with internet access to produce a solution, graded fairly and reproducibly by TAs without requiring paid AI subscriptions.

## Language

### The project

**Project Type A (Mastery Project)**:
A project where the graded object is the solution itself and AI is a permitted tool; the student's understanding of course content is assured by the difficulty of getting a correct solution, not by TA inspection.
_Avoid_: AI-assisted project, traditional project

**Project Type B (Specification Project)**:
A project where the graded object is a specification the student writes, and correctness is judged by executing that specification through the reference harness.
_Avoid_: prompt project, prompt-engineering assignment

**Hybrid Project**:
A project that grades the submitted solution (as Type A) and runs the specification through the reference harness only as a reproducibility gate. The shape of the previous project, made checkable.
_Avoid_: prompt-plus-code project

**Part**:
One independently contracted, tested and weighted component of a multi-part project (e.g. Part II, alpha-beta, 35%). Each part is its own project directory.
_Avoid_: section, stage, milestone (collides with the Milestone)

**Specification**:
The student-authored text that, given to a harness, is meant to produce a correct solution. The artifact of a Type B project.
_Avoid_: prompt, LLM prompt (a specification may be several files, not one message)

**Published Resource**:
A document, dataset, or endpoint at a URL the professor controls that the task depends on and the harness must retrieve. Where the twist lives.
_Avoid_: internet resource, external data

**Twist**:
The deliberate deviation from the well-known version of a problem (the altered nine men's morris board) that makes training-data recall insufficient.
_Avoid_: variation, modification

### Execution and grading

**Harness**:
An agentic tool that runs a model with tool access (shell, file edits, web fetch), e.g. a CLI coding agent. Distinct from a bare chat interface.
_Avoid_: agent, LLM, chatbot, model (the model is one component of a harness)

**Reference Harness**:
The one specific free-to-use harness and model configuration the TAs execute every submission with. The only harness whose output contributes to the grade.
_Avoid_: official tool, grading model

**Regeneration**:
A TA-side execution of a submitted specification through the reference harness. A submission may be regenerated several times to account for nondeterminism.
_Avoid_: re-run, retry, attempt

**Reproducible**:
Property of a regeneration whose model weights, seed, and temperature are pinned so that rerunning it yields the same result unless a tool result or the published resource changed.
_Avoid_: deterministic (agent loops with web access are never fully deterministic)

**Hidden Test Suite**:
Tests held by the TAs and not shown to students, run against the solution a regeneration produces.
_Avoid_: grading tests, secret tests

**Public Test Suite**:
Tests given to students with the assignment so they can check their own work against the interface contract.
_Avoid_: sample tests, examples

**Test Category**:
A named group of hidden tests (e.g. "twist edge cases", "malformed input"). Categories and counts are shown to students; cases are not.
_Avoid_: test group, section

**Best-of-K**:
The regeneration policy: K regenerations at a fixed temperature schedule, the grade taken from the regeneration with the highest hidden-test pass rate.
_Avoid_: best-of-N, retries

**Equivalence Policy**:
A named rule, per test category, for what counts as a pass: `strict`, `estimate`, `ab`, or `valid`. Replaces the phrase "functionally identical."
_Avoid_: functionally identical, correctness criterion

**Interface Contract**:
The fixed shape every generated solution must have (language, entry point, input and output format) so one test suite can run against every submission.
_Avoid_: API, spec (collides with Specification)

### Evidence and review

**Ledger**:
An append-only text file on the professor's website that harnesses write entries to. Evidence that the harness retrieved and followed the published resource.
_Avoid_: access log, audit trail

**Ledger Entry**:
One line in the ledger, signed with a student ID, recorded when a harness follows the published resource's instruction to sign.
_Avoid_: log line, record

**Student ID**:
The institutional identifier in the form `XXXNNNNNN` (three letters, six digits) used to sign ledger entries.
_Avoid_: username, netid

**Nonce**:
A random string printed on the published resource that a ledger entry must carry. Proof the page was read, not merely the endpoint hit.
_Avoid_: token, secret, key

**Run Tag**:
A label on a ledger entry saying which execution produced it: `practice` for a student's own run, `grading-k1..k3` for TA regenerations, `appeal` for an appeal run.
_Avoid_: label, source

**Variant**:
A per-student parameter carried in the resource URL that alters the twist and the generated hidden tests. Optional integrity measure.
_Avoid_: seed (collides with the regeneration seed), version

**Slot**:
One of the K regeneration conditions: a fixed temperature paired with a fixed secret seed, realised as a pinned model.
_Avoid_: run (a run is one execution in a slot), attempt

**Calibration Run**:
The professor's pre-release execution of the reference specification through the reference harness; the gate that the task is solvable by the graded model.
_Avoid_: dry run, pilot

**Process Note**:
A short student-written account of how they used the harness and what their process was. Collected with every submission.
_Avoid_: reflection, AI usage log, blurb

**Written Component**:
The page-limited, human-graded part of a submission, scored on a 3–4 point rubric. Distinct from the process note.
_Avoid_: essay, report

**Safety Read**:
The mandatory human reading of every specification before regeneration, to catch malicious instructions planted by the student or injected into their workflow.
_Avoid_: review, screening

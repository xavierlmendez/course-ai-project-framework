# AI-Assisted Course Project Framework

A reusable framework for course projects in which students direct an AI harness with internet access to produce a solution, graded fairly and reproducibly by TAs without requiring paid AI subscriptions.

This file is the glossary. Every other document uses these terms exactly, and none of them is defined here by how a tool implements it: the definitions say what a thing *is*, `tools/README.md` says how it is spelled on disk.

## Language

### The project

**Project Type A (Mastery Project)**:
A project where the graded object is the solution itself and AI is a permitted tool; the student's understanding of course content is assured by the difficulty of getting a correct solution, not by TA inspection.
_Avoid_: AI-assisted project, traditional project

**Project Type B (Specification Project)**:
A project where the graded object is a specification the student writes, and correctness is judged by executing that specification through the reference harness.
_Avoid_: prompt project, prompt-engineering assignment

**Hybrid Project** (**not provided**; see framework.md §15):
A project that would grade the submitted solution as Type A and run the specification through the reference harness only as a pass/fail reproducibility gate. The shape of the previous project. The framework does not provide it: no handout, no runner mode, no gate column, no test. A professor who wants it builds that runner mode themselves. "Hybrid" is therefore never the answer to "which type is this project"; the answer is A or B.
_Avoid_: prompt-plus-code project, Type H

**Program**:
One independently contracted, tested and weighted unit of work: one entry point, one specification (Type B) or one solution (Type A), one set of test categories, one project directory. A program is what the tools grade and what a weight in `parts.json` names.
_Avoid_: module, deliverable

**Part**:
One of the professor's weighted components of the assignment as students meet it (Part II, alpha-beta, 35%). A part may group more than one program. The professor's four parts of example 01 group **eight programs** — an Opening and a Game program each — so its `parts.json` has eight entries and its directories are `part-<N>-opening/` and `part-<N>-game/`. Where a part contains exactly one program the two words coincide, which is why the tools spell a program directory `part-<name>`.
_Avoid_: section, stage, phase

**Specification**:
The student-authored text that, given to a harness, is meant to produce a correct solution. The artifact of a Type B project, one per program.
_Avoid_: prompt, LLM prompt (a specification may be several files, not one message)

**Published Resource**:
A document, dataset, or endpoint at a URL the professor controls that the task depends on and the harness must retrieve. Where the twist lives.
_Avoid_: internet resource, external data

**Twist**:
The deliberate deviation from the well-known version of a problem (the altered nine men's morris board) that makes training-data recall insufficient.
_Avoid_: variation, modification

**All-Twist Part**:
A program whose graded categories are *all* twist categories, so the rule that twist weights sum to half of the non-graduate weights holds trivially. Allowed, but only when the professor declares it deliberately; otherwise it reads as a weighting mistake.
_Avoid_: fully twisted, pure-twist

### Execution and grading

**Harness**:
A program that runs a model in a loop with tool access (shell, file edits, web fetch), e.g. a CLI coding agent. Distinct from a bare chat interface. The model is one component of a harness; "the agent loop" is the loop inside one.
_Avoid_: agent, LLM, chatbot, coding assistant — "the agent loop" is the one accepted use

**Reference Harness**:
The one specific free-to-use harness and model configuration the TAs execute every submission with, chosen each semester against the **six criteria** in framework.md §5 (free for every student, built-in web fetch, headless, temperature-settable, model-pinnable, and emitting structured tool calls as measured). The only harness whose output contributes to the grade.
_Avoid_: official tool, grading model

**Regeneration**:
A TA-side execution of a submitted specification through the reference harness. A submission may be regenerated several times to account for nondeterminism.
_Avoid_: re-run, attempt

**Slot**:
One of the K regeneration conditions: a fixed temperature paired with a fixed secret seed, realised as a pinned model. Slots are numbered 1..K and named `k1`..`k<K>` wherever a run has to be identified.
_Avoid_: run — a run is one execution in a slot

**Seed**:
The integer that fixes a slot's random draw, so the same slot rerun gives the same regeneration back. One per slot, secret until grades are released and published afterward with the hidden tests. A seed is never written into a run record and never printed by a tool. Not to be confused with a **variant**, which is the per-student parameter.
_Avoid_: key, salt, random state

**num_ctx**:
The context window each slot's model is pinned to. It is a correctness parameter, not tuning: the agent loop's system prompt and tool schemas do not fit the model server's small default, and a slot that overflows silently truncates the prompt. The framework's instance pins 32,768.
_Avoid_: context length, window size

**Reproducible**:
Property of a regeneration whose model weights, seed, temperature, and harness-plus-wrapper-prompt are pinned, so that rerunning it yields the same result unless a tool result or the published resource changed. It says nothing about wall clock, which belongs to the machine.
_Avoid_: deterministic (agent loops with web access are never fully deterministic)

**Best-of-K**:
The regeneration policy: K regenerations at a fixed temperature schedule, the grade taken from the regeneration with the highest hidden-test pass rate.
_Avoid_: best-of-N, retries

**Practice Run**:
A student's own execution of the grading path on their own machine: the same wrapper prompt and temperature schedule, the public suite instead of the hidden one, seeds of the student's own instead of the secret ones, no sandbox, and the run tag `practice`. It is what the milestone is built from, and it can never produce or overwrite a grading record.
_Avoid_: test run, trial run, local run

**Dry Run**:
A run that prints the command lines it would execute and executes nothing. Its record is kept, because it is the easiest way to see exactly what would run, but it is named apart (`*.dry.json`) and no grading, milestone or combining step reads one. A dry run is not a practice run and is not evidence of anything having happened.
_Avoid_: simulation, no-op run, pilot

**Run Tag**:
The label saying which execution produced a run and its ledger entry. The vocabulary is `grading` (a TA batch), `practice` (a student's own run), `appeal` (a granted appeal), and `calibration` (the professor's pre-release run). For a Type B regeneration the slot is appended, so a tag on the wire reads `grading-k1`, `practice-k1`, `appeal-k2`, `calibration-k3`.
_Avoid_: label, run type

**Milestone**:
The early, auto-graded gate worth 10 points: evidence that the student got the reference setup working and that their work passes the **public** suite through it. A milestone is a signed record — signed in the sense that its contents are digested so that editing it is detectable, not in the sense of a cryptographic identity — naming the student, the program, the model and the public-suite result. On a Type B project the record must additionally carry **harness evidence**: the completed regeneration run that produced the code being measured. A digest proves the record was not edited; it does not prove the run happened, because the student controls the machine.
_Avoid_: checkpoint, deadline

**Hidden Test Suite**:
Tests held by the TAs and not shown to students, run against the solution a regeneration produces.
_Avoid_: grading tests, secret tests

**Public Test Suite**:
Tests given to students with the assignment so they can check their own work against the interface contract. The suite a practice run and the milestone use.
_Avoid_: sample tests

**Test Category**:
A named group of hidden tests (e.g. "twist edge cases", "malformed input"), carrying a weight and an equivalence policy. Categories and counts are shown to students; cases are not.
_Avoid_: test group

**Equivalence Policy**:
A named rule, per test category, for what counts as a pass: `strict`, `estimate`, `ab`, or `valid`. Replaces the phrase "functionally identical". Anything other than `strict` is realised by the category's own checker; a category whose declaration and directory disagree is refused rather than graded on the wrong rule.
_Avoid_: functionally identical, correctness criterion

**Interface Contract**:
The fixed shape every generated solution must have (language, entry point, input and output format) so one test suite can run against every submission.
_Avoid_: API

**Environment Failure**:
A regeneration that did not happen because the machine was broken — model server unreachable, container runtime down, disk full, out of memory. The slot is left incomplete with the reason recorded and is not scored; re-running the same command retries it. Never a student's zero.
_Avoid_: crash, infrastructure error

**Harness Error**:
A regeneration in which the harness exited cleanly, made no tool call and produced no entry point. Nothing was specified badly; the loop never began. Treated exactly like an environment failure — incomplete, unscored, retried — and it is the failure the sixth harness criterion exists to catch before a cohort meets it.
_Avoid_: model failure, empty run

**Student Failure**:
A run that completed on a working machine and still did not clear the tests: the specification (or the solution) is what fell short. This is the only one of the three that becomes a score.
_Avoid_: bad prompt, user error

**Circuit Breaker**:
The rule that stops a batch after three consecutive environment failures. An isolated failure leaves one slot incomplete and the batch carries on; a run of them means the machine, not the cohort, is what needs fixing, and continuing would mark everybody incomplete against a dead model server.
_Avoid_: abort threshold, kill switch

**ollama_host / ollama_host_local**:
Two addresses for the one model server. `ollama_host` is the address as the **grading sandbox** reaches it, and it belongs to the grading run; `ollama_host_local` is the address as **this machine** reaches it, and it is the one key a student on a shared course server sets in their own copy. A student running the model locally sets neither. An environment variable does not substitute for either. Say which of the two you mean; neither is "the model URL".
_Avoid_: model URL

### Evidence and review

**Ledger**:
An append-only, **write-only** text file on the professor's website that harnesses add entries to. Write-only means entries go in and the file is never served back: it holds student identifiers and client addresses and is read by course staff on the server. Evidence that the harness retrieved and followed the published resource.
_Avoid_: access log, audit trail

**Ledger Entry**:
One line in the ledger, signed with a student ID, recorded when a harness follows the published resource's instruction to sign. It carries a timestamp, the student ID or pair, a run tag, any variant, and the client address. It does **not** carry the nonce: the nonce is what was required in order to write the entry at all, so there is nothing to match on afterwards.
_Avoid_: log line

**Student ID**:
The institutional identifier in the form `XXXNNNNNN` (three letters, six digits) used to sign ledger entries. A pair is two of them, written `A+B` in the ledger, `A-B` as a directory name, and `A,B` in a roster; the three forms name the same submission.
_Avoid_: username, netid

**Nonce**:
A random string printed on the published resource that a ledger entry must carry in order to be accepted. Proof the page was read, not merely the endpoint hit. One per semester, rotated with the twist.
_Avoid_: token, key

**Roster**:
A list the **professor** supplies that the tools cannot derive from the project directory: who is a graduate student, who is enrolled, and — for a Type A project using variants — which variant each submission gets (`variants.csv`). The roster decides; a claim inside a student's submission does not.
_Avoid_: class list, enrolment file

**Variant**:
A per-student parameter carried in the resource URL that alters the twist and the generated hidden tests. Optional integrity measure, assigned by the roster.
_Avoid_: seed (that is the regeneration seed), version

**Similarity Check**:
The **institution's** existing plagiarism checker, to which the course submits specifications (Type B) or solutions (Type A) under the standard misconduct process. The framework ships no similarity tool of its own and names the institution's in the handout.
_Avoid_: plagiarism detection, MOSS (that is one instance of it)

**Calibration Run**:
The professor's pre-release execution of the reference specification through the reference harness; the gate that the task is solvable by the graded model, and the source of the timeouts and the appeals answer key. Type A calibrates without a harness run, on the same page of the checklist.
_Avoid_: pilot, trial

**Process Note**:
A short student-written account of how they used the harness and what their process was. Collected with every submission, one per submission.
_Avoid_: reflection, AI usage log

**Written Component**:
The page-limited, human-graded part of a submission: three dimensions (accuracy, twist specificity, candor) scored 0–3 each, and a fourth (prediction) for graduate submissions. Course-level — written once and scored once, however many programs the project has. Distinct from the process note.
_Avoid_: essay, report

**Safety Read**:
The mandatory human reading of every specification before regeneration, to catch malicious instructions planted by the student or injected into their workflow. An integrity and course-policy check: the sandbox, not the read, is the safety control.
_Avoid_: screening

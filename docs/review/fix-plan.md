# Fix plan — course-ai-project-framework review

Status: **approved 2026-09-08** · Written 2026-09-08 · Owner: Xavier Mendez · Brief: `docs/review/brief.md` · Findings: `docs/review/findings.md`

This was the human gate from `engineering-standards/playbooks/evidence-to-plan.md` §8. Approved by Xavier on 2026-09-08 with the decisions in §2. Execution is phase at a time, reviewed at each boundary.

## 0. Why

The framework is structurally sound and its examples work: every reference solution passes its hidden suite, every canonical solution fails the twist categories, and the deterministic checks pass. What the review found is that the **documents and the tools disagree with each other**, and on grading day the tools win. A TA who follows the runbook exactly produces a gradebook missing 30 of 100 points, grades every graduate on the undergraduate bar, and silently denies appeals. A student who follows example 01's handout exactly scores zero. None of that is visible until the semester it happens.

The end state: a professor and two TAs can run this project for 130 students without asking the author anything, and every number in a gradebook can be traced to a rule stated in a document that matches the code.

## 1. Success criteria

1. `pytest` suite exists and passes, covering every contract a finding broke: grad handling, missing written/milestone rows, empty categories, best-of-K selection, part combination, appeal re-runs, pair directories, variant sources, malformed test cases, and slot argument bounds.
2. A scripted end-to-end rehearsal grades a fixture cohort (undergraduate, graduate, a pair, a variant student, a crashed run, an appeal) and produces a gradebook whose every column is checkable by hand against the rubric.
3. `scripts/review_checks.py` passes with zero FAIL rows, including the twist-weight rule and a declared equivalence policy per category.
4. A TA following `templates/ta-runbook.md` verbatim on example 01 and example 04, with no other knowledge, reaches a complete gradebook. Verified by a fresh-context agent that may read only the repo.
5. A student following example 02's handout and the primer verbatim reaches a passing milestone. Same verification method.
6. The sandbox denies: a solution reading `/tests`, any outbound TCP except the two allowed host-port pairs, outbound DNS to a non-allowlisted resolver, and outbound IPv6. Each proven by a test that fails before the fix.
7. Every claim in `framework.md` about a tool's behaviour is exercised by a test or marked unimplemented in the options menu.

## 2. Decisions

All confirmed by Xavier on 2026-09-08 in the review conversation. Numbered for reference from the slices below.

1. **Fix direction.** Where a document states the intended policy, the tool changes; where the tool is right, the document changes. The brief's settled decisions arbitrate. No settled decision is reopened.
2. **Tests first.** The test suite arrives in the same slice as the first tool fix it guards (`CONTRIBUTING` behavioural-baseline rule).
3. **Multi-part arithmetic.** A part contributes only its hidden-test score, weighted by part weight, to the 70. Milestone (10) and written (20) are course-level and counted once. A perfect multi-part student scores exactly 100.
4. **Example 01 Parts III and IV are built out.** Black-move and improved-estimation programs get resources, hidden tests, reference and canonical solutions, matching the professor's real four-part project. This is the largest slice in the plan.
5. **Hybrid is demoted.** It stays in the options menu marked "not provided, build it yourself", leaves the settled-decisions list and the active glossary, and no handout promises it.
6. **Similarity detection points at the institution's tool.** The handout names the university's existing check and the runbook adds a submission step. No homegrown score to defend.
7. **Type B submissions carry the specification plus data files it explicitly names.** Anything executable in the target language is stripped before the harness runs. The word cap counts the named data files.
8. **The roster is authoritative for variants.** The runner reads the variant from `variants.csv` by student ID and ignores any `variant.txt` in a submission. The handout tells students where to find theirs.
9. **Grading runs on one dedicated box over a longer window.** The runbook's stated budget comes from the calibration run's measured time, not a guess, and the timeout follows the calibration rule of twice the reference run.
10. **Environment failures do not score.** A slot that fails for environment reasons is marked incomplete and the batch continues. **Three consecutive failures abort the batch loudly** so the TA fixes the environment. A retry pass picks up incomplete slots. Harness-produced failures (a specification that did not work) still score zero.
11. **The milestone is a signed runner record.** The runner emits a record (public-suite results, harness version, timestamp, student ID) that the student submits; a checker validates it and writes `milestone.csv`.
12. **The rubric gains a mechanical decision rule per band** plus one worked example drawn from the shipped sample submissions. Granularity stays 0 to 3.
13. **Execution is phase at a time**, with Xavier reviewing between phases against the stated exit criteria.
14. **Git.** The framework repo gets an initial commit of today's state so fixes can be diffed against what the review examined; Xavier pushes. Every slice after that is a branch and a PR. The portfolio changes become their own branch.
15. **No fixed deadline.** All six phases run in order; correctness beats speed.
16. **The two artifacts are republished once**, after Phase 5, when the documents they summarise are correct.
17. **Example 01 ships all eight programs**, an Opening and a Game variant for each of the four parts, matching the professor's assignment. This roughly doubles slice 5.4's test and solution work.
18. **Part IV is graded against positions where the baseline estimator is weak.** The professor picks positions the handout's estimator misjudges; hidden tests require the improved program to choose the better move there and stay legal everywhere else.
19. **A multi-part submission is one directory with per-part specification files** (`SPEC-part-I.md` and so on) plus one process note and one written component. The runner learns to map a part to its specification filename; the wrapper prompt becomes part-specific.
20. **Tests use the standard library's `unittest`.** The zero-dependency promise is what makes the tools readable on a bare lab machine, and it outweighs matching the engineering-standards pytest config.
21. **The Type A calibration gate** is the deterministic one: reference passes every hidden test, a canonical solution ignoring the twist fails the twist categories, and per-case timings set the test timeout. No harness run required.
22. **Stray output removed and example seeds rotated** (2026-09-08), after the recursive-copy bug was found to have written 20 copies of the seeds file into an example's output tree. Nothing had reached git.
23. **The R620 is the harness verification machine**, container `harness-01` (LXC 102, 192.168.2.12). Measurement on 2026-09-08 confirmed it: the temperature path works, and at 3.07 tok/s it cannot grade a cohort. Decision 9's dedicated grading machine is **still to be named** and is now the plan's largest open decision; the options and the throughput target are in `docs/review/evidence/grading-box.md`.
24. **F-65 is resolved, not fixed.** The schedule reaches the model today only because OpenCode omits the temperature field. This makes pinning the OpenCode version (F-10) a correctness control rather than a hygiene one, and slice 2.6's self-check must assert the effective temperature differs across slots by observation.

## 3. Unknowns

- ~~Whether an actual OpenCode regeneration behaves as the runner assumes.~~ Partly answered 2026-09-08 on the R620: the provider configuration is right, the model and slot pinning work, and the temperature path holds. Still unmeasured: how a full agentic regeneration behaves under the real timeout, which needs a machine fast enough to finish one.
- **Which machine grades.** The R620 is too slow by roughly 8 to 10×. Named options are in `docs/review/evidence/grading-box.md`; this blocks the runbook's time budget (decision 9) and therefore Phase 3.
- Whether the professor's cluster storage class supports the volume mode the ledger needs. Phase 6 states the requirement; only a deploy confirms it.
- Whether two TAs actually score the rubric's Candor row consistently once decision 12 lands. Only calibration against real submissions settles it; the plan ships the decision rule, not the proof.
- What the real regeneration wall-clock time is on the grading box. Decision 9 makes the runbook's number come from measurement, so the number is unknown until the first calibration run.

## 4. Current state

- Deterministic checks: `docs/review/checks-2026-09-08.md`. All four examples' reference solutions pass; all canonical solutions fail twist categories; 10 FAIL rows, all in example 01 Parts III/IV weights and undeclared policies, plus the missing test suite.
- Judges and verification: 127 proposed, 107 confirmed, 7 rejected, 21 unverified. `docs/review/findings.md`.
- The repository has no commits (F-53). The portfolio changes are uncommitted.

## 5. Phases and slices

Decider for every phase: **Xavier**. Each slice is one branch, one PR, one end-to-end piece with its test.

### Phase 0 — Complete the inputs · exit when: the finding list is closed and the harness path is proven or documented · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 0.1 | — | Re-verify the 21 unadjudicated findings | — | **Done 2026-09-08**: 20 stand, 1 dropped, 5 new issues |
| 0.2 | — | Remove stray output, rotate example seeds | — | **Done 2026-09-08** |
| 0.3 | `chore/baseline-commit` | Initial commit of today's state so fixes diff against what the review examined; Xavier pushes | 0.2 | Repo has a first commit; `git log` shows one baseline |
| 0.4 | — | Stand up an LXC on the R620 with Ollama and OpenCode, pull the 14B model, and measure whether per-slot temperature and seed reach the model (F-65) | SSH key on the R620 | **Done 2026-09-08**: they do. OpenCode 1.18.29 sends no temperature, so the Modelfile governs. Evidence in `docs/review/evidence/f65-temperature-path.md`. Measured 3.07 tok/s; the R620 cannot be the grading box (`evidence/grading-box.md`) |

### Phase 1 — Grading arithmetic is correct and tested · **DONE 2026-09-08** · exit criteria met: 55 tests green, rehearsal exits 0 with every row matching hand arithmetic · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 1.1 ✅ | `test/tools-baseline` | Add `tests/`, fixtures for a cohort (undergrad, grad, pair, variant, crashed run), and characterization tests that record today's behaviour including the wrong parts, marked `xfail` where a later slice fixes them | — | `pytest -q` green; every Phase 1 finding has a test that currently fails |
| 1.2 ✅ | `fix/grad-column` | `grad` column in the runbook, the rubric, and a roster template; `grade.py` fails loudly when `status.csv` lacks it rather than defaulting to 0 | 1.1 | F-02 test passes; a graduate fixture scores on the graduate denominator |
| 1.3 ◐ | `fix/written-milestone-path` | Runbook produces `written.csv` and `milestone.csv`; every `grade.py` invocation passes both; `grade.py` refuses to emit `total` when a component is missing and marks the row incomplete (decision 11 defines the milestone input) | 1.1 | F-03, F-16 tests pass; the rehearsal gradebook totals 100 |
| 1.4 ✅ | `fix/combine-parts` | Combine hidden scores by part weight, then add milestone and written once (decision 3) | 1.3 | F-04 test passes; a perfect multi-part student scores exactly 100 |
| 1.5 ✅ | `fix/appeal-records` | Key run records on run tag; an appeal writes its own record; `grade.py` prefers it; runner refuses to silently skip | 1.1 | F-05, F-14 tests pass; an appeal changes the grade in the rehearsal |
| 1.6 ✅ | `fix/run-integrity` | Environment failure marks the slot incomplete and the batch continues; a circuit breaker aborts on three consecutive failures; a retry pass resumes incomplete slots (decision 10). Clamp written dimensions; bound `--slot`; one malformed case fails one case | 1.1 | F-13, F-17, F-18, F-57 tests pass; a fixture with three consecutive environment failures aborts, one isolated failure does not |
| 1.7 ✅ | `fix/submission-isolation` | Type B copies the specification plus the data files it names, stripping executables (decision 7); the runner refuses a submission path that contains its own output directory or a `project.json`; variants read from `variants.csv` by student ID (decision 8); Type A code excluded from the word cap | 1.1 | F-11, F-12, F-46 tests pass; a submission containing `solve.py` cannot influence a Type B grade; pointing `--submission` at a project directory is refused rather than copying secrets; an edited `variant.txt` has no effect |
| 1.8 ✅ | `feat/multi-part-specs` | The runner maps a part to its specification file (`SPEC-part-I.md`), and the wrapper prompt names it (decision 19) | 1.1 | A four-part submission in one directory grades correctly; F-01 is resolved by the layout rather than by renaming |

**Phase 1 result.** One commit, `fix(tools): phase 1`. 55 standard-library tests, 28 of which failed
before the change. `scripts/rehearsal.py` grades a fixture cohort (perfect undergraduate, graduate on
the wider denominator, twist failure, a pair, a missed milestone, an ungraded written component, an
environment failure, a granted appeal) and every total matches arithmetic computed independently of
the tools. The four examples still pass their hidden suites and their canonical solutions still fail
the twist categories. Findings closed: F-02, F-03, F-04, F-05, F-11, F-12, F-13, F-14, F-16, F-17,
F-18, F-25, F-46, F-47, F-57, and F-50's missing-test-suite half. Slice 1.3 is marked ◐ because the
tool half is done and the runbook half (actually producing `written.csv` and `milestone.csv`) belongs
to slice 3.1.

One design conflict surfaced during the rehearsal and was resolved: the new completeness rule marked
every *part* incomplete, because a part has no milestone or written component by design. `grade.py`
gained a hidden-only mode, implied by a `part` key in `project.json`.

### Phase 2 — The grading environment is sealed and pinned · **DONE 2026-09-08** · exit criteria met: 11 sandbox tests, 6 of which failed before the fix; 67 tests green overall · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 2.1 ✅ | `fix/sandbox-network` | Per-host-port allow rules, DNS restricted to the resolver, IPv6 denied by default | 1.1 | F-08, F-09, F-49 tests pass from inside a built image |
| 2.2 ✅ | `fix/hidden-test-isolation` | The graded solution cannot read the expected outputs: run tests as a separate user with `/tests` unreadable to the solution, or feed one case at a time | 2.1 | F-07 test passes: a lookup solution scores zero |
| 2.3 ✅ | `fix/pin-harness` | Pin the OpenCode version in the Dockerfile and record it in `project.json`; the timeout kills the container, not the client | 1.1 | F-10, F-15 tests pass; two builds a week apart produce the same harness version |
| 2.6 ✅ | `fix/temperature-path` | Set temperature and seed in the generated config as well as the Modelfile, and have the runner read back the model's effective parameters before grading (F-65) | 0.4 | The self-check fails loudly when a slot's effective temperature differs from its schedule |
| 2.7 ✅ | `fix/entrypoint-ownership` | Stop chowning the bind mount; run as the unprivileged user without rewriting host ownership (F-62) | 1.1 | Resume can delete a working directory after a sandboxed run on Linux |
| 2.4 ✅ | `fix/seed-hygiene` | Seeds not printed by `--create-slots`, not stored in run records before release | 1.1 | F-52 test passes |
| 2.5 ✅ | `fix/prescan` | `--allow` defaults from `project.json` so conforming specifications are not flagged; add the missed classes; document what it does not catch | 1.1 | F-24, F-25 tests pass; sample submissions are `OK`, a planted specification is `FLAG` |

**Phase 2 result.** One commit, `fix(sandbox): phase 2`. `tests/test_sandbox.py` builds the image and
runs containers; six of its eleven tests failed against the sandbox as it stood, and two more passed
at first for the wrong reason and were rewritten until they could fail. Findings closed: F-07, F-08,
F-09, F-10, F-15, F-24, F-49, F-52, F-62, and F-65's guard.

Two things worth recording. The isolation fix was wrong on the first attempt: the tests were staged
to a root-only copy while the read-only mount stayed world-readable beside it, so a solution could
still read the answers through the mount. The end-to-end test caught what the permission test missed.
The mount now lives inside `/root`, which the graded user cannot traverse. Second, isolation depended
on every caller passing `--run-as`; forgetting it silently ran the solution as root. `run_tests.py`
now drops privileges by default whenever it is root, so the safe path is the default one.

### Phase 3 — A TA can execute the runbook cold · exit when: a fresh-context agent grades example 01 and example 04 from the repo alone · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 3.1 | `docs/runbook-rewrite` | Rewrite the runbook against the fixed tools: serve the resource, create slots after seeds arrive, set `graded`, the real time budget, multi-part order, pair and variant naming, ledger gate without the nonce, the page cap in words | Phase 1, Phase 2 | F-19, F-20, F-21, F-22, F-40, F-41, F-42, F-43 addressed; every command runs as written |
| 3.2 | `feat/milestone-tool` | The runner emits a signed milestone record; a checker validates submitted records and writes `milestone.csv` (decision 11) | 3.1 | F-39 test passes; `milestone.csv` is produced from student records, not typed |
| 3.3 | `docs/rubric-sharpen` | A mechanical decision rule per band plus one worked example from the shipped submissions (decision 12) | 3.1 | F-44 addressed; two fresh-context graders score the same sample within one point |

### Phase 4 — A student can reach the milestone from the handout and primer · exit when: a fresh-context agent does so · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 4.1 | `fix/student-commands` | One practice command that works without secret seeds or pre-created slots, defaulting to the public suite; fix the shared-server instructions to the setting OpenCode actually honours | Phase 2 | F-29, F-30, F-31 tests pass |
| 4.2 | `docs/handout-truth` | Fill every placeholder, name only files that exist, link the primer, correct the specification filename, remove the promise of programs that do not exist | 4.1 | F-01, F-28, F-33, F-60 addressed |
| 4.3 | `docs/primer-corrections` | Remove instructions the sandbox cannot satisfy; make the wrapper text match the project's entry point | 4.1 | F-32 addressed |

### Phase 5 — The framework's promises match what it ships · exit when: no document promises an unimplemented behaviour · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 5.1 | `feat/equivalence-policy` | `policy` in the schema, consumed by the test runner and checked by `review_checks.py`; declared on every category in all four examples | Phase 1 | F-34 test passes; checks report zero policy FAILs |
| 5.2 | `fix/calibration-gate` | Calibration runs from a directory holding only the specification; add the variants path and the Type A path (decision 21); fix the step ordering that requires seeds before creating them | Phase 1 | F-06, F-38, F-63, F-64 addressed; a gate cannot pass with the solution present |
| 5.3 | `fix/hybrid-and-similarity` | Demote Hybrid to "not provided" in the options menu, out of settled decisions and the active glossary (decision 5); point similarity detection at the institution's tool with a runbook step (decision 6) | — | F-36, F-37 addressed; no handout promises an absent mechanism |
| 5.4a ✅ | `feat/example-01-eight-programs` | Add the Game (midgame/endgame) program to Parts I and II, so both program shapes exist under the established contract (decision 17) | 5.1 | Reference passes; canonical fails twist categories; hopping and capture paths are covered |
| 5.4b ✅ | `feat/example-01-eight-programs` | Build Part III, Opening and Game for Black (decision 17) | 5.4a | Same bar; the colour-swap contract is exercised |
| 5.4c ✅ | `feat/example-01-eight-programs` | Build Part IV, Opening and Game with the improved estimator, graded on positions where the baseline is weak (decisions 17, 18) | 5.4b | Same bar; a submission that simply copies the baseline estimator fails |
| 5.4d ✅ | `feat/example-01-eight-programs` | Correct the twist weights and claims across all four parts; re-scope Part II's twist category so it tests the board twist rather than textbook pruning, and replace its straw-man canonical | 5.4b | F-26, F-27, F-54 addressed; checks report zero weight FAILs |
| 5.5a | `fix/example-01-resource` | Correct the worked example that prints a wrong expected output (F-61), and the same class of error across the other resources | 5.1 | Every worked example reproduces from its reference solution |
| 5.5 | `fix/twist-weight-enforcement` | Enforce the twist-half rule in `review_checks.py` and state the rule for an all-twist part | 5.4 | F-35 addressed |

**Slices 5.4a–d result (2026-09-08).** One commit on `feat/example-01-eight-programs`. Example 01 is
now eight program directories — `part-<N>-opening` and `part-<N>-game` for each of the four parts —
because a project directory carries one `entry`. `parts.json` weights them 22.5/22.5/17.5/17.5/5/5/5/5,
which is the professor's 45/35/10/10 split evenly within each part. Every program has a reference
solution, a canonical solution, a `<1,500`-word `reference/SPEC.md`, a generated hidden and public
suite, a sample submission and a gitignored seeds file, and every category declares a `policy`. All
eight references reproduce the professor's own recorded outputs in `AISpring26/tests/spec.yaml`
exactly. Every reference passes every hidden case; every canonical scores under 50% on its twist
category. Part II's twist category is now `ab_*_mill`, positions where a diagonal-spoke mill decides
the move under pruning, and its canonical is a fair alpha-beta on the standard board rather than
minimax-without-pruning. Findings closed: F-26, F-27, F-28, F-54. `review_checks.py --no-network`
reports zero FAIL rows.

### Phase 6 — Records, portfolio, and consistency · exit when: the repo is committed, CI is green, and the site deploys · decider: Xavier

| Slice | Branch | Change | Depends on | Done when |
|---|---|---|---|---|
| 6.1 | `chore/repo-standards` | `CLAUDE.md`, `docs/DECISIONS.md` from the existing ADRs, `docs/BACKLOG.md`, CI running the tests and checks, pre-commit | Phase 1 | F-50 addressed; CI green on a PR |
| 6.2 | `fix/portfolio-ledger` | Volume permissions, redeploy strategy, atomic header write, client address from the socket, align validation with the reference server, decision records | — | F-23, F-51, F-55, F-56 addressed; a deploy dry-run writes an entry |
| 6.3 | `fix/ledger-server-hardening` | Path containment by real path, ledger default outside any repository, ignore rule | — | F-47, F-48 tests pass |
| 6.4 | `docs/consistency` | Reconcile stale numbers, the schema documentation, run-tag vocabulary, the artifact, and terminology against `CONTEXT.md` | Phases 1–5 | F-58, F-59 addressed; a fresh-context consistency judge returns PASS |
| 6.5 | `docs/reproducibility-statement` | State what reproducible means including the machine, and what is not fixed | Phase 2 | F-45 addressed |

## 6. Risks

| Risk | Trigger | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| Fixing tools breaks the four examples | A Phase 1 slice changes grading arithmetic | High | Examples stop demonstrating the framework | Slice 1.1's characterization tests run on all four examples every slice | Xavier |
| The sandbox hardening cannot be tested without the model | Phase 2 needs a running harness | Medium | Escape tests are written but never exercised end to end | Test the network and filesystem controls with a stub container; the model is not needed for either | Xavier |
| Phase 5 stalls on decisions only the professor can make | Assumptions 4 and 5 unconfirmed | Medium | Phases 1–4 ship, 5 does not | Ask both questions before Phase 3 ends; demotion is the default if no answer | Xavier |
| The 21 unverified findings hide a real blocker | A verifier never adjudicated them | Medium | A blocker ships | Re-run verification for those 21 before Phase 1 closes | Xavier |
| Scope grows into a rewrite | 60 issues invite restructuring | Medium | Nothing ships before the semester | Slices are fixes, not redesigns; no settled decision is reopened | Xavier |

Top three reasons this plan fails:

1. **The examples are treated as fixtures and quietly rot** while the tools change under them. Mitigated by running all four in every slice's tests (risk 1).
2. **Phase 3 and 4 are declared done by reading rather than by execution.** The exit criteria require a fresh-context agent to actually reach a gradebook and a milestone; reading the document is not the test (criteria 4 and 5).
3. **The unverified 21 are forgotten** because the confirmed list is long enough to feel complete (risk 4).

## 7. Immediate next actions

1. ~~Approve the plan~~ — approved 2026-09-08, with the sixteen decisions in §2.
2. Re-verify the 21 unadjudicated findings so Phase 1 starts from a complete list. **In progress.**
3. ~~Remove stray output and rotate example seeds~~ — done 2026-09-08 (decision 22).
4. Initial commit of today's state for Xavier to push (decision 14). **Next.**
5. Get SSH key access to the R620 so slice 0.4 can run (decision 23). **Blocked on Xavier.**

Xavier reviews at every phase boundary (decision 13).

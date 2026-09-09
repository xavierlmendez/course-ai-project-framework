# Brief for the professor — the AI-harness project framework

Prepared 2026-09-09 by Xavier Mendez. The repository is
`github.com/xavierlmendez/course-ai-project-framework`; start with `framework.md`. This page says
what the framework is, what has been verified, and the decisions that are yours.

## What it is, in one paragraph

A reusable way to set a course project in which students direct an AI harness that can read a
resource you publish on the web, and to grade the result fairly with two TAs. Each project is a
**published resource** (the rules, on a page you control) plus a **twist** (a change to the
textbook version that a model cannot know from training data) plus an **interface contract**
(how the program is run) plus **public and hidden tests** in weighted categories. Students submit
either code (**Type A**, graded once) or a **specification** that the course's reference harness
regenerates into code (**Type B**, graded on the best of three runs at fixed temperatures with
secret seeds). Every submission also signs a write-only **ledger** on your page, proving the
harness fetched the resource. Grades are 10 milestone, 70 hidden tests (the twist categories carry
half), 20 written page scored by decision rules. Nothing costs a student money: the reference
harness is OpenCode running a local open-weights model through Ollama.

## What ships

- `framework.md` (the design and your workflow), a glossary, seven design-interview transcripts.
- Templates: handouts for both types, the TA runbook (three days, every command), the rubric with
  decision rules and worked examples, calibration and rotation checklists, a student primer.
- Tools, Python standard library only: pre-scan, resource and ledger server, runner (sandboxed
  regeneration with a fixed schedule), grading, multi-part combination, milestone records,
  fan-out from the student layout, plus 234 unit tests and a rehearsal script.
- Four worked examples. Example 01 is your Spring 2026 Morris-variant project recast as Type B:
  all eight programs, each with a reference solution that reproduces your recorded outputs exactly,
  a canonical (untwisted) solution that fails the twist categories, and generated test suites.

## What has been verified

| Claim | Evidence |
|---|---|
| Grading arithmetic matches hand calculation for a fixture cohort of eight cases | `scripts/rehearsal.py` |
| The sandbox blocks everything but the resource page and the model server | 11 sandbox tests, green on an AWS g5.xlarge |
| The reference model emits structured tool calls | qwen3:14b: 5 of 5 probes; qwen2.5-coder:14b: 0 of 5 (ruled out) |
| A full Type B regeneration completes through the harness | R620 (CPU): nine tool calls, program written, ledger signed; GPU timing in §Late results |
| Throughput on a g5.xlarge (A10G) | 49.5 tokens per second; a 300-token answer in 6 seconds |
| A TA can grade from the runbook alone | seven cold runs by a fresh reader; the grading path ran clean on the seventh, the rehearsal path is fixed as of that run |
| A student can reach the Type A milestone from the handout alone | third cold walk: no guesses needed |

Three real defects in the harness stack were found and worked around in the runner: OpenCode's
five-minute provider timeout, OpenCode reading its project directory from the shell's `PWD`, and
qwen3's thinking mode, which makes the model narrate its plan and end the turn without acting.
The slot Modelfiles now carry a patched template that disables thinking.

## Decisions that are yours

1. **Should the repository stay public?** Example 01 contains complete solutions and hidden
   tests for your live assignment. Options: make it private and share access, or move that
   example's solutions out of the public tree.
2. **Reference model.** `qwen3:14b` with thinking off is the proven instance. Thinking on would
   change every timing number and has not completed a run.
3. **Grading machine.** The timeouts and the grading-day budget in the runbook are defined "as
   measured on the grading machine". A g5.xlarge on AWS (about one dollar an hour) ran the
   verification; the calibration run for your reference specification should happen on whichever
   box will grade.
4. **One written page per project.** For a multi-part project the student writes one `WRITTEN.md`
   and one `PROCESS.md` for the whole project, scored once. The sample submission ships that way.
5. **All-twist programs.** The handout template says "twist categories carry 35 of the 70". A
   program whose categories are all twist categories makes that sentence false; the tools allow
   it if you declare it, but the handout wording for that case is yours to choose.
6. **Similarity checking.** The example handouts name MOSS; the templates leave a placeholder.
7. **Pairs.** Pairs are allowed by the tools (IDs joined by `+`); whether your course allows them
   is your call.
8. **The prior project's description.** `docs/research/prior-project-spring-2026.md` paraphrases
   your handout and grading checklist. Say if you would rather it were not public.

## What happens next

- You run the calibration gate on your reference specification (`templates/calibration-checklist.md`):
  it must clear every hidden test in at least one of the three slots before release.
- A TA rehearses the runbook with the shipped samples before grading day (the runbook's
  "Rehearsing with the shipped samples" note).
- Each semester: change the twist and rotate the seeds (`templates/rotation-checklist.md`).

## Late results

(GPU regeneration timing appended when the run finishes.)

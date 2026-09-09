# ADR 0003: The specification, not the runner, carries the ledger sign instruction

**Date:** 2026-09-08 · **Status:** accepted

## Context

The published resource instructs the harness to sign the ledger with the student's ID. In Type B the TA runs the regeneration, so someone must supply that instruction and the ID. The runner could inject both for every student, which would make the ledger measure only whether the harness followed the resource.

## Decision

The student's specification is responsible for telling the harness to fetch the resource and sign the ledger with the student's ID. The runner adds only a run tag through the environment (`RUN_TAG`), which the resource tells the harness to include, so grading entries are distinguishable from practice entries.

## Consequences

- The specification remains the whole graded object. "Did the harness use the internet as instructed" is a property of the specification, which is what Type B measures.
- A specification that omits the instruction produces no ledger entry. For Type B this is informational (the twist categories already reflect a harness that never read the resource); for Type A it is a gate.
- The handout must state the requirement in one bold line, since it is the most likely thing to be forgotten for reasons unrelated to skill.

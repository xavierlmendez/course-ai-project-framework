# ADR 0002: Best-of-K at a fixed temperature schedule with secret per-slot seeds

**Date:** 2026-09-08 · **Status:** accepted

## Context

A specification run through a model is nondeterministic. One run is a lottery; unlimited runs reward effort and luck rather than the specification. The professor wants students to have the best chance, and wants the previous complaint about uncontrolled temperature answered directly.

## Decision

K=3 regenerations at temperatures 0.2, 0.6, 1.0, identical for every student. Each slot has a fixed seed, secret until grades are released and published afterward with the hidden tests. The hidden-test score is the **best** of the three.

## Alternatives considered

- **Median of K** rewards robust specifications and is arguably what Type B measures; rejected because the professor chose to favour students, and the fixed schedule already makes best-of-K fair.
- **Published seeds** would let students reproduce grading runs exactly; rejected because it invites seed-fitting.
- **Unfixed seeds** would make appeals impossible to rerun.

## Consequences

- Every specification faces the same three conditions; that is the fairness argument in one sentence.
- Machine time is 3× a single run; at 65 submissions and ~10 minutes each it is an overnight batch.
- A single crashed or timed-out run costs nothing if another run passes.

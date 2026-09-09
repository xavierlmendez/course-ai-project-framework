# ADR 0001: The course owns the execution; the reference harness is a local, pinned model

**Date:** 2026-09-08 · **Status:** accepted

## Context

The previous project graded code that students generated with whatever model they had. Three failures followed: uncontrolled temperature, per-student best-of-N with different N, and an advantage for students with paid model access. A cloud free tier (Gemini CLI) was the obvious fix for cost, but its free tier may reroute models mid-session, exposes no seed, and is capped per account per day, so regenerations would not be reproducible and appeals could not rerun a grade.

## Decision

Grades come only from executions the course performs. The reference harness is chosen under five published criteria (free for every student, built-in web fetch, headless, temperature-settable, model-pinnable). This year's instance is OpenCode on Ollama with `qwen2.5-coder:14b`, with per-slot models pinned by Modelfile `temperature` and `seed`.

## Consequences

- Reproducible regenerations: an appeal or regrade reruns bit-for-bit unless a tool result or the published resource changed.
- The graded model is weaker than frontier cloud models, so the professor must calibrate every task against it (ADR-adjacent rule in framework.md §7). Tasks that need frontier capability do not fit this framework.
- Hardware becomes the equity question instead of subscriptions. Mitigated by the lab, the SSH server, and the runner's server-address parameter.
- Switching to a cloud harness later is a one-line change in `project.json` but forfeits reproducibility; the handout would have to say so.

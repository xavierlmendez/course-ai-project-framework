# What machine can run the grading batch

Measured 2026-09-08 on the R620 (`harness-01`, LXC 102, 16 cores of 2 × Xeon E5-2670 v1,
32 GB of the host's 125 GB, no GPU). Slice 0.4 of `docs/review/fix-plan.md`.

## Measurement

| Quantity | Value |
|---|---|
| Generation rate, `qwen2.5-coder:14b` | **3.07 tokens/second** (120 tokens in 38 s) |
| CPU instruction set | AVX only. **No AVX2**, no AVX-512, no GPU |
| Model size on disk | 9.0 GB |
| Host memory | 125 GB, so the model is nowhere near the limit |

The host's own operations notes predicted this in their open decision 3: "no AVX2 and there is no GPU;
CPU inference of small models is possible but slow (expect single-digit tokens/s for 7B-class at
4-bit)." A 14B model lands at the low end of that.

## What it means for grading

The framework's batch is K=3 regenerations for every submission. At 65 students per TA that is 195
regenerations, and each is an agentic loop of several turns, not a single completion.

At 3.07 tokens/second, a regeneration producing even 5,000 output tokens takes about 27 minutes,
before counting prompt processing and tool round-trips. That exceeds the framework's default
20-minute timeout on its own. A full cohort would take on the order of a hundred hours.

**Verdict: the R620 verifies, it does not grade.** It is the right machine for slice 0.4's question,
for calibration rehearsals, and for any correctness check that does not care about wall clock. It
cannot be the dedicated grading box that decision 9 assumes.

## What the grading box needs

Sizing from the same batch: 195 regenerations inside one overnight window of roughly 12 hours means
about 3.7 minutes per regeneration, so roughly **8 to 10× this machine's throughput**, in the region
of 25 to 30 tokens/second for a 14B model at 4-bit.

Options, in rough order of cost:

| Option | Note |
|---|---|
| A consumer GPU with 12 GB or more of VRAM | A 14B model at 4-bit fits in 12 GB and reaches tens of tokens/second. The cheapest path to the target. |
| An Apple Silicon machine with unified memory | The M2 Pro already benchmarked ~4.5× the R620 per core on other work; its memory bandwidth suits inference far better than DDR3-1066. |
| A smaller reference model | Dropping to a 7B-class model roughly doubles throughput on the same hardware, at the cost of the reference harness following a specification less reliably. This changes a settled decision and would need re-calibration. |
| A longer grading window | Decision 9 already accepts "one dedicated box, longer window". Two or three nights on a faster CPU box may suffice without a GPU. |

This is an open decision for Xavier and is recorded as such in the fix plan.

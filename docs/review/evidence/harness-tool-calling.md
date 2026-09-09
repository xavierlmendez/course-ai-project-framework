# The reference harness cannot drive an agentic loop with the chosen model

Measured 2026-09-08 on macOS (M2 Pro), Ollama 0.12.x, OpenCode 1.18.29 in the sandbox image,
`qwen2.5-coder:14b`. Found by the third cold TA run of the runbook; verified directly here.

## What happens

A real Type B regeneration on `examples/01-morris-type-b/part-I`, sandbox on, slot 1:

```
$ python3 tools/runner.py --project part-I/project.json \
    --submission part-I/submissions/ABC123456 --slot 1 --run-tag probe --out runs/
1 submissions, type B, sandbox=on
  ABC123456 k1: temperature=0.2 tag=probe-k1
done                                             # 42 s
```

The record:

```
entry_present: false      harness_exit: 0      environment_error: null
complete: true            tests: {"solution_started": false, "categories": {},
                                  "error": "no entry point produced"}
```

The working directory afterwards holds `SPEC.md` and `opencode.json` and nothing else. The
harness's own event stream says why:

```json
{"type":"text","part":{"text":"{\n  \"name\": \"Read\",\n  \"arguments\": {\n    \"filePath\": \"./SPEC.md\"\n  }\n}"}}
{"type":"step_finish","part":{"reason":"stop","tokens":{"input":2050,"output":25}}}
```

The model **wrote the tool call as assistant text** instead of calling the tool, then stopped
after 25 output tokens. The agent loop never began.

## It is the model, not the configuration

Both of Ollama's endpoints, asked directly with a tool definition:

```
POST /v1/chat/completions   finish_reason: stop   tool_calls: null
                            content: {"name": "read_file", "arguments": {"path": "SPEC.md"}}
POST /api/chat                                    tool_calls: null
                            content: {"name": "read_file", "arguments": {"path": "SPEC.md"}}
```

Five consecutive attempts through `/api/chat` with an explicit "use the read_file tool"
instruction: **five text-only replies, zero structured tool calls.**

This is not a provider or transport problem. It is not intermittent.

## Why the capability flag is misleading

```
$ ollama show qwen2.5-coder:14b
  Capabilities:  completion   tools   insert
$ ollama show --template qwen2.5-coder:14b | grep -c -i tool
16
```

Ollama advertises `tools` and the chat template does render tool definitions into the prompt.
What the model does not do is emit its call in the form the template's parser expects (Qwen's
`<tool_call>…</tool_call>` wrapper); it emits bare JSON, which Ollama returns as ordinary
content. The capability flag describes the template, not the model's behaviour.

## Consequences for the framework

1. **The reference harness instance in `framework.md` §5 does not work.** OpenCode plus
   `qwen2.5-coder:14b` cannot fetch the published resource, cannot sign the ledger, and cannot
   write the entry point, because it cannot call a tool. Every Type B regeneration produces
   nothing.

2. **The runner scores that as the student's failure.** `classify_failure` recognises only
   environment errors, so a harness that ran and produced nothing is recorded `complete` with
   a hidden score of zero. A cohort graded on this setup would receive 65 zeros with no
   indication in the gradebook that the machine, not the specifications, was at fault.

3. **The calibration gate is what should have caught this** (`framework.md` §7): the
   professor's reference specification must clear every hidden test before release, and here
   it would clear none. The gate works; it had simply never been run, because no machine in
   this project had the model until now. This is the failure the gate exists for, found one
   step late.

## The context-size theory, tested and refuted

OpenCode's provider documentation says tool calls that arrive as text are usually a context
problem: Ollama defaults to 4096 tokens and the tool schemas alone exceed it, so raise
`num_ctx` to 16k–32k. Tested on the R620 (16 cores, 32 GB, the model fully in RAM at 32k):

| `num_ctx` | structured tool calls, 5 attempts |
|---|---|
| 4096 | 0 |
| 32768 | 0 |

Identical text-only replies at both sizes (`docs/review/evidence/cpu-run/tooltest-*.txt`).
Context is not the cause. The runner nevertheless now carries `num_ctx` into the slot
Modelfiles, because 4096 is too small for an agent loop regardless of which model is chosen.

A side observation from the same run: at 32k the 14B model occupies 15 GB rather than 9,
which on a 16 GB laptop spills to CPU and swaps. Whatever model is chosen, the "students run
the reference harness on their own machines" story needs either an 8B-class model or the
shared server.

## What does not change

The rest of the design is unaffected: the pinning, the seeds, the temperature schedule, the
sandbox, the grading arithmetic and the ledger are all independent of which model is chosen.
What must change is the **model**, and the framework's five criteria for a reference harness
need a sixth: *the model must emit structured tool calls*, verified before the semester, not
assumed from a capability flag.

## The replacement model, tested (2026-09-09, R620)

Same box, same Ollama 0.33.3, same prompt and tool definition, `"think": false`:

| model | `num_ctx` | structured tool calls, 5 attempts | generation |
|---|---|---|---|
| `qwen2.5-coder:14b` | 4096 | 0 | 3.07 tok/s |
| `qwen2.5-coder:14b` | 32768 | 0 | |
| `qwen3:14b` | 32768 | **5** | 3.75 tok/s |

Every `qwen3:14b` reply is a real `tool_calls` entry
(`docs/review/evidence/cpu-run/tooltest-qwen3-32k.txt`), and Ollama reports the model's
capabilities as `completion, tools, thinking`. The reference harness instance therefore
changes from `qwen2.5-coder:14b` to `qwen3:14b`; the sixth criterion above was applied
before the swap rather than assumed.

## A second, separate defect: OpenCode's five-minute silence limit

The "Unexpected server error" the runner saw on the R620 had a different cause, visible only
with `opencode run --print-logs --log-level DEBUG`
(`docs/review/evidence/cpu-run/opencode-diag.log`):

```
level=ERROR message="stream error" providerID=ollama modelID=qwen3:14b
  error.error="ProviderHeaderTimeoutError: Provider response headers timed out after 300000ms"
```

OpenCode 1.18.29 aborts any provider request whose response headers, or next streamed
chunk, take longer than 300 s. A 14B model on a CPU-only box spends longer than that
evaluating the harness's first prompt (the system prompt plus tool schemas), so every
regeneration died at exactly five minutes, before the first token. The installed binary reads
two provider options, `headerTimeout` and `chunkTimeout` (milliseconds, or `false` to
disable; both default to 300000), so the runner now writes both into the generated
`opencode.json` as `regeneration_timeout_s × 1000`. The runner's own wall-clock kill is the
only bound that should apply. A GPU box would rarely hit the limit, but a slot that stalled
would still have been mis-scored as the student's failure rather than an environment one, so
the fix is not CPU-specific.

## Solved (2026-09-09, R620)

Even on `qwen3:14b` with a 32k context and the header timeout lifted, a full run still made
zero tool calls. Six experiments on the R620 (CPU-only, Ollama 0.33.3, OpenCode 1.18.29;
`docs/review/evidence/cpu-run/night6-1.txt` … `night6-4.txt`, timings in `night6-log.txt`)
found the cause and a fix that runs the whole course workflow end to end.

**Root cause: thinking mode, not the harness.** With thinking on, `qwen3:14b` narrates its
entire tool plan inside `<think>`, closes the block and emits end-of-turn with zero tool calls
and zero content. Captured through a logging proxy (experiment 1, 723 s, no tool call, no
file). It is not a tool-schema, context-window, streaming or timeout problem: the same body
replayed with thinking off produces a tool call on the first turn. It is also ~13x cheaper —
372 thinking tokens became 29 useful ones for the same decision.

**Two dead ends.** `PARAMETER think false` is rejected by Modelfiles. A `"think": false` field
in the request body is silently ignored by Ollama's `/v1/chat/completions`, which is the
endpoint OpenCode talks to — replays with `think:false` streaming, non-streaming, and both,
all still returned zero tool calls (experiments 2a–2c, ~230 s each).

**The fix: patch the slot's TEMPLATE.** The stock qwen3 template already carries the no-think
machinery, but both halves are gated behind `$.IsThinkSet`, which `/v1` never sets. Two edits
make it unconditional:

- **A** — the block `{{- if and $.IsThinkSet (eq $i $lastUserIdx) }} … /think … /no_think …
  {{- end }}` becomes an unconditional ` /no_think` appended to the last user message.
- **B** — `{{ if and $.IsThinkSet (not $.Think) -}}` becomes `{{ if true -}}`, so the empty
  `<think>\n\n</think>\n\n` prefill is always emitted.

Builder used on the night: `docs/review/evidence/cpu-run/night6-mkmodel.py`; the resulting
Modelfile is `night6-Modelfile.nothink`.

**The successful run.** Experiment 4a: the real captured OpenCode body (10 tools), non-stream,
981 s — `finish_reason: tool_calls`, no `reasoning` key at all. Experiment 4b: a full OpenCode
run, 06:13:13→06:40:53, wall 1660 s, rc 0 — the agent loop ran to completion, nine tool calls
over nine steps and the program written; content was a stub only because nothing was serving
the course page. Experiment 4c, with `ledger_server.py` actually serving
`examples/01-morris-type-b` on 8080: the agent read `SPEC.md`, fetched the course page (200,
5580 bytes), wrote 4546 bytes of real Python, ran it, iterated — **and signed the ledger**
(`2026-09-09T08:10:26+00:00  ABC123456  night6  127.0.0.1`). It was still iterating when the
5400 s cap fired. The only remaining limitation is speed: turn 3 alone took ~55 minutes at
~3.7 tok/s, so a CPU grading box needs `regeneration_timeout_s` in hours, not the GPU-shaped
1200.

**Runner change.** `runner.py` now owns this. The project key `thinking` defaults to `"off"`;
`--create-slots` reads `ollama show --template <base_model>`, applies patches A and B
(`no_think_template()`, which stops with a clear message if either anchor is missing) and
writes the result as a `TEMPLATE """…"""` block in every slot Modelfile after the PARAMETER
lines. `--verify-slots` reads the slot's template back and reports "slot N still thinks:
re-run --create-slots". `"thinking": "default"` leaves the template untouched, for a base
model with no thinking mode. Recorded as D-007 in `docs/DECISIONS.md`.

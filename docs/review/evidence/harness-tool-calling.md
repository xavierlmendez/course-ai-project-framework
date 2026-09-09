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

## What does not change

The rest of the design is unaffected: the pinning, the seeds, the temperature schedule, the
sandbox, the grading arithmetic and the ledger are all independent of which model is chosen.
What must change is the **model**, and the framework's five criteria for a reference harness
need a sixth: *the model must emit structured tool calls*, verified before the semester, not
assumed from a capability flag.

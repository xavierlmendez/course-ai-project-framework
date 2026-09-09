# F-65 resolved: the per-slot temperature and seed do reach the model

Measured 2026-09-08 on the R620 (`harness-01`, LXC 102), Ollama 0.33.3, OpenCode 1.18.29,
`qwen2.5-coder:14b`. Slice 0.4 of `docs/review/fix-plan.md`.

## The concern

`tools/runner.py` pins temperature and seed per slot by building an Ollama model from a Modelfile
(`create_slots`), then names that model in the generated `opencode.json`. Nothing sets a temperature
in the request itself. If OpenCode sent its own default temperature on every call, it would override
the Modelfile value, all three best-of-K slots would run at the same temperature, and the framework's
stated 0.2 / 0.6 / 1.0 schedule would be fiction.

## What was measured

**1. A request-level temperature does override the Modelfile.** Same slot model
(`PARAMETER temperature 0.0`, `PARAMETER seed 4242`), same prompt, four calls each:

| Request | Result |
|---|---|
| no `temperature` field | `Dog`, `Dog`, `Dog`, `Dog` |
| `"temperature": 1.5` | `Elephant`, `Elephant`, `Elephant`, `Elephant` |

The answer changes, so the request value wins when present. (Output stays constant within each group
because the Modelfile seed is still applied.)

**2. Ollama reports the effective parameters.** `POST /api/show` on a slot model returns
`"seed 4242\ntemperature 0"`, which gives the runner a way to assert the pin before grading.

**3. OpenCode does not send a temperature.** A logging proxy was placed between OpenCode and Ollama
and OpenCode was run with exactly the configuration `runner.py` generates. Both requests it issued:

```
{"path": "/v1/chat/completions", "keys": ["max_tokens","messages","model","stream","stream_options"],
 "temperature": "<ABSENT>", "top_p": "<ABSENT>", "seed": "<ABSENT>", "model": "ref-test-slot1"}
{"path": "/v1/chat/completions", "keys": ["max_tokens","messages","model","stream","stream_options","tool_choice","tools"],
 "temperature": "<ABSENT>", "top_p": "<ABSENT>", "seed": "<ABSENT>", "model": "ref-test-slot1"}
```

Raw capture: `opencode_requests.jsonl`.

## Conclusion

**The design works as documented on OpenCode 1.18.29.** The Modelfile's temperature and seed govern,
because OpenCode omits both fields. F-65's mechanism is real but does not currently fire.

**It is version-fragile.** One OpenCode release that starts sending a default temperature would
silently flatten the schedule to three seeds at one temperature, with no error and no visible symptom.
Two consequences for the plan:

- Pinning the OpenCode version (F-10, slice 2.3) is not only about prompt stability. It is what keeps
  the temperature schedule working at all. Raise its priority accordingly.
- The slice 2.6 self-check should assert by observation, not only by reading `/api/show`: issue one
  probe through the harness path per slot and confirm the effective temperature differs across slots,
  failing loudly if they match.

## Incidental finding

OpenCode issues a second model call with a `title` agent (`small=true`) to name the session, before
the task call. On a slow model that is pure overhead inside the regeneration timeout. Worth disabling
if the configuration allows it.

## Hardware verdict

3.07 tokens/second generating with the 14B model (120 tokens in 38 s). The host has AVX but no AVX2
and no GPU. See `docs/review/evidence/grading-box.md`.

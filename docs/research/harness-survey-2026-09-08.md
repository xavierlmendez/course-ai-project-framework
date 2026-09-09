# Survey: zero-cost agentic coding harnesses with web tools and headless runs

Surveyed 2026-09-08 by a research sub-agent. Every claim cites a source (S#). "Unverified" = not confirmed on a vendor page. Free allowances change often; re-verify before each semester.

> **Note added 2026-09-09 (the survey itself is left as it was written).** This table's last row
> recommends `qwen2.5-coder` sizes on RAM grounds, and the model chosen from it on 2026-09-08 was
> `qwen2.5-coder:14b`. That choice was wrong for a reason no column here captures: measured on
> 2026-09-09, the model returns its tool call as assistant text rather than a structured `tool_calls`
> entry (0/5 at `num_ctx` 4096 and 0/5 at 32768), so an agent loop never starts. The reference model
> is now **`qwen3:14b`** (5/5 at 32768). The survey therefore needs a column it does not have —
> *emits structured tool calls, measured* — which is the sixth criterion added to `framework.md` §5.
> Sizes also assume Ollama's 4096-token default context; at the 32,768 the agent loop requires, a 14B
> model occupies about 15 GB rather than 9. See `docs/review/evidence/harness-tool-calling.md` and
> D-006 in `docs/DECISIONS.md`.

| Harness (vendor) | Free-tier terms | Web fetch/search built in | Headless / scripted | Temp / seed | Free-tier model(s) | Pin model version |
|---|---|---|---|---|---|---|
| **Claude Code** (Anthropic) | Not on Free plan; Pro/Max only [S1]. No individual student plan; Campus Program gives API credits to club members via student ambassadors [S5]; institutional "Claude for Higher Education" via sales [S6]. | Yes: `WebFetch`, `WebSearch` [S3] | `claude -p "…" --output-format json` [S2] | No temperature/seed flag [S2]; request closed as duplicate [S4] | None free (needs Pro/Max or API credits) [S1] | Yes, `--model claude-…` full name [S2] |
| **Gemini CLI** (Google) | Google sign-in: 1,000 requests/day, no card; free API key: 250/day, Flash only [S7] | Yes: `google_web_search`, `web_fetch` [S9] | `gemini -p "…" --output-format json` [S8] | Temperature/topP via `modelConfigs…generateContentConfig`; no seed documented [S11] | Gemini family "as determined by Gemini CLI" (Google login) / Flash (API key) [S7] | `-m/--model` or `model.name` setting [S10]; free tier may reroute models [S7] |
| **Codex CLI** (OpenAI) | Included in ChatGPT Free at $0 [S12]; Free limits not listed on the pricing page [S12]; "10–100 msgs/5h" claim is unverified [S15]. Edu plan = contact sales [S12]. | Yes: `--search` (live) or default `web_search="cached"` [S13,S14] | `codex exec "…"` [S13] | No temperature/seed keys in config reference [S14] | ChatGPT-plan models [S12,S13] | `-m/--model` or `model` in config.toml [S13,S14] |
| **GitHub Copilot CLI** (GitHub) | "All plans include Copilot CLI" incl. Copilot Free [S16,S21]. **Copilot Student**: verified students, unlimited completions, 200 AI credits/mo since Jun 1 2026 [S18]. Teachers may get Pro free [S16]. | `web_fetch` tool exists [S20]; no web *search* documented (unverified) | `copilot -p "…" --allow-all-tools` [S17] | No temperature setting documented [S17] | Free/Student: **auto model selection only** [S16,S19] | `--model` exists [S17] but not honored on Free/Student [S19] |
| **Aider** (open source) | Tool is free; cost = model provider (Gemini API free key, Groq, OpenRouter `:free`, or Ollama) [S22,S25] | `/web` scrapes a URL only; no search [S23] | `aider --message "…" --yes` [S22] | `extra_params: temperature:` in `.aider.model.settings.yml` [S24] | Whatever provider you point it at | Yes, `--model provider/name` [S22,S25] |
| **OpenCode** (SST) | Tool free; Zen free models are "limited time" and Zen sign-up requires **billing details** [S29]; BYO Ollama/OpenRouter/Groq keys [S30] | Yes: `webfetch`, `websearch` [S27] | `opencode run "…" --format json --model p/m` [S26] | `temperature` per agent in config; no seed [S28] | Zen free (rotating) or BYO provider [S29,S30] | Yes, `--model provider/model` [S26] |
| **Goose** (Block/AAIF) | Tool free; provider docs cite Gemini free tier, Groq free open-weight models, Ollama; Tetrate gives $10 credits [S33] | No native web tool documented; web via MCP extensions — secondary source [S34] | `goose run --no-session -t "…" --with-builtin developer` [S31] | `GOOSE_TEMPERATURE` (0.0–1.0); no seed [S32] | BYO provider [S33] | `GOOSE_MODEL` env var [S32] |
| **Cline CLI** (Cline) | Free models rotate "limited-time", need a Cline account; quota unspecified [S36]; otherwise BYO key [S35] | `fetch_web` tool [S37]; websearch for Cline-provider users [S38] | `cline --json --auto-approve … -m model -P provider` [S35] | Not documented (unverified) [S35] | Rotating promo model [S36] | `-m/--model` per run [S35] |
| **Roo Code** | Extension shut down; repo archived May 15 2026 [S39] | — | — | — | — | — |
| **Local: Ollama + Aider/OpenCode/Goose** | $0; qwen2.5-coder 7b = 4.7 GB, 14b = 9 GB fit 16 GB RAM [S46]; qwen3-coder:30b = 19 GB does not [S47]. Aider `ollama_chat/<model>` [S25]; OpenCode Ollama provider [S30]; Goose `goose configure` → Ollama [S48] | Ollama web_search/web_fetch API free with Ollama account, limits undocumented [S45]; harness must wire it via MCP (unverified) | Via harness flags above | Per harness (Aider/OpenCode/Goose all expose temperature) [S24,S28,S32] | Any local GGUF | Yes, by tag |

## Free API-credit providers

| Provider | Terms |
|---|---|
| Anthropic | No general free API tier found; Campus Program credits via clubs [S5]; no individual student plan [S1,S5] |
| Google AI Studio | Free tier on `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.x-flash` etc.; `gemini-3.1-pro-preview` not free [S43]; per-model RPM/RPD shown only after login [S44]; no-card claim unverified |
| OpenRouter `:free` | 20 RPM; 50 req/day with <$10 lifetime credits, 1,000/day once ≥$10 ever purchased [S40] |
| Groq | Free plan per model, e.g. `openai/gpt-oss-120b` and `qwen/qwen3.6-27b`: 30 RPM, 1K RPD, 8K TPM, 200K TPD [S41]; "no credit card" from secondary source only [S42] |
| Ollama cloud web search | Free account, "generous free tier", limits undocumented [S45] |

## Caveats

- Free allowances are volatile: OpenCode Zen and Cline free models are explicitly "limited time" [S29,S36]; Gemini CLI free tier may switch models mid-session [S7].
- Only Gemini CLI, Aider, OpenCode, and Goose expose temperature; none documents a seed [S11,S24,S28,S32]. Claude Code, Codex, Copilot expose neither [S2,S14,S17].
- Copilot Free/Student cannot pin a model (auto only) [S19]; Gemini CLI free tier and Cline free promo reroute/rotate models [S7,S36].
- Codex Free limits and Groq no-card status could not be confirmed on vendor pages.
- Daily caps (Gemini 250–1,000, OpenRouter 50, Groq 1K) bound batch throughput; limits are per account/org, not per key [S7,S40,S41].

## Sources

S1 https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan · S2 https://code.claude.com/docs/en/cli-reference · S3 https://code.claude.com/docs/en/tools · S4 https://github.com/anthropics/claude-code/issues/6096 · S5 https://claude.com/programs/campus · S6 https://claude.com/solutions/education · S7 https://geminicli.com/docs/resources/quota-and-pricing/ · S8 https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md · S9 https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/web-search.md · S10 https://google-gemini.github.io/gemini-cli/docs/get-started/configuration.html · S11 https://geminicli.com/docs/cli/generation-settings/ · S12 https://learn.chatgpt.com/docs/pricing · S13 https://learn.chatgpt.com/docs/developer-commands?surface=cli · S14 https://learn.chatgpt.com/docs/config-file/config-reference · S15 https://www.morphllm.com/codex-pricing · S16 https://docs.github.com/en/copilot/concepts/billing/individual-plans · S17 https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically · S18 https://github.com/orgs/community/discussions/189268 · S19 https://github.blog/changelog/2026-06-24-changes-to-model-selection-for-free-and-student-plans/ · S20 https://github.com/github/copilot-cli/discussions/1950 · S21 https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals · S22 https://aider.chat/docs/scripting.html · S23 https://aider.chat/docs/usage/commands.html · S24 https://aider.chat/docs/config/adv-model-settings.html · S25 https://aider.chat/docs/llms/ollama.html · S26 https://opencode.ai/docs/cli/ · S27 https://opencode.ai/docs/tools/ · S28 https://opencode.ai/docs/agents/ · S29 https://opencode.ai/docs/zen/ · S30 https://opencode.ai/docs/providers/ · S31 https://goose-docs.ai/docs/tutorials/headless-goose/ · S32 https://goose-docs.ai/docs/guides/environment-variables/ · S33 https://goose-docs.ai/docs/getting-started/providers/ · S34 https://www.scrapeless.com/en/blog/goose-scrapeless-mcp · S35 https://docs.cline.bot/usage/cli-overview · S36 https://docs.cline.bot/getting-started/free-models · S37 https://docs.cline.bot/tools-reference/all-cline-tools · S38 https://cline.bot/blog/cline-3-48-0-skills-and-websearch-make-cline-smarter · S39 https://github.com/RooCodeInc/Roo-Code · S40 https://openrouter.ai/docs/api-reference/limits · S41 https://console.groq.com/docs/rate-limits · S42 https://www.getaiperks.com/en/ai/groq-free-tier-2026 · S43 https://ai.google.dev/gemini-api/docs/pricing · S44 https://ai.google.dev/gemini-api/docs/rate-limits · S45 https://docs.ollama.com/capabilities/web-search · S46 https://ollama.com/library/qwen2.5-coder · S47 https://ollama.com/library/qwen3-coder · S48 https://github.com/ollama/ollama/blob/main/docs/integrations/goose.mdx

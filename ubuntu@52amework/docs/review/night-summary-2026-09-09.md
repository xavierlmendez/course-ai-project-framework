# Overnight summary, 2026-09-09 — for Xavier to review and confirm

Written by the orchestrating session while Xavier was away. Everything below is on the
integration branch `feat/phase-3-ta` (local; nothing pushed) unless marked otherwise.
Items marked **CONFIRM** need Xavier's decision or action; the rest is reported for review.

## 1. What was merged tonight (all into `feat/phase-3-ta`, tests green at every merge)

| Slice | What | Evidence |
|---|---|---|
| 5.1 equivalence policy | `policy` on every category; `run_tests.py --project`; checks enforce it | `tests/test_policy.py` |
| 5.2 calibration gate | gate runs from a directory holding only the specification; Type A path | `tests/test_runner.py` |
| 5.3 + 5.5 | Hybrid demoted; similarity step against the institution's tool; twist-half rule enforced with `all_twist` | `scripts/review_checks.py` |
| Phase 6 | `CLAUDE.md`, `CONTRIBUTING.md`, `docs/DECISIONS.md`, `docs/BACKLOG.md`, CI, pre-commit; ledger refuses a path inside a repo | `.github/workflows/ci.yml` |
| Phase 4 | `runner.py --practice`; `ledger_server.py --project`; primer and handouts filled | `tests/test_handouts.py` |
| 5.4 | example 01 rebuilt as **eight programs** (`part-<N>-opening`, `part-<N>-game`), every reference reproduces the professor's recorded outputs exactly | `examples/01-morris-type-b/` |
| 5.6 | reference model → **qwen3:14b** (D-006); sixth harness criterion; OpenCode timeout and PWD fixes; `num_ctx` in slot Modelfiles | `docs/review/evidence/harness-tool-calling.md` |
| 4.4 / 4.5 | Type B milestone needs the harness record that produced the code; `ollama` calls and the no-sandbox OpenCode URL use the host-side server; one-sentence errors for missing binaries and busy ports; dry-run records are `*.dry.json`; per-project milestone filename | `tests/test_phase4_defects.py`, `tests/test_phase4c_defects.py` |
| 3.4 / 3.5 | cold-run fixes: per-part notes survive `combine_parts.py`; pair matching on any member; `tools/fan_out.py` bridges the student layout to per-program grading; runbook rewritten around `{{PROJECT_JSON}}`, `resource_port`, `[course]`/`[per part]` marks | `tests/test_fan_out.py` |
| 6.2 (portfolio repo) | branch `feat/course-ai-framework` in `~/develop/portfolioWebsite`: ledger route mirrors the reference server, `Recreate` strategy, fsGroup, 22 vitest tests, decision record | `xavis_projects/app/lib/projectUtils/courseAiFramework/` |
| 6.4 consistency | glossary, framework, templates and both artifacts reconciled; judge verdict PASS with six items reserved (see §4) | `docs/review/fix-plan.md` §6.4 |

Test state at the last merge: fast suite green, `scripts/rehearsal.py` exit 0,
`scripts/review_checks.py` **0 FAIL** (`docs/review/checks-2026-09-09.md`).

## 2. Decisions taken without you (CONFIRM each)

1. **Reference model is `qwen3:14b`, not `qwen2.5-coder:14b`.** Measured on the R620:
   qwen2.5-coder never emits a structured tool call through Ollama (0/5 at two context sizes);
   qwen3 does (5/5). Recorded as D-006 with a sixth harness criterion.
2. **qwen3's thinking mode is left at Ollama's default** (D-007, status *open*). See §3 — this is
   the unresolved item.
3. **Example handouts name MOSS** as the similarity checker (templates keep `{{SIMILARITY_TOOL}}`).
4. **Students submit multi-part work in one directory** (`<id>/<program>/SPEC.md` plus one
   `WRITTEN.md` and one `PROCESS.md`); `tools/fan_out.py` produces the per-program directories the
   runner needs. The example 01 sample now ships in that layout.
5. **Ledger check for Type B happens after the batch** (entries appear as the harness runs); a
   student with no `grading-k<N>` entry is noted for the professor. Type A keeps the pre-batch gate.
6. **Phases 3 and 4 are not marked done.** Six cold TA runs and three cold student walks were run;
   each found defects, all fixed. Type A student path is clean (walk 3: no guesses). The Type B
   student path and the TA runbook were still producing new findings on the last run, so the
   plan says "exit criterion not yet met" rather than claiming it.

## 3. The one thing that is NOT proven: an end-to-end Type B regeneration

No model has yet completed the agent loop inside OpenCode on the R620:

- `qwen2.5-coder:14b`: writes the tool call as text; never calls a tool. Ruled out.
- `qwen3:14b`: calls tools when asked directly (5/5), but inside OpenCode it produced a
  *reasoning* part of ~400–560 tokens ("First, I should use the Read tool…") and then stopped
  without calling one, in two runs (thinking on; `/no_think` in the prompt did not disable it;
  Ollama Modelfiles reject a `think` parameter).
- Two real OpenCode defects were found and fixed on the way: a 300 s provider header timeout
  (runner now sets `headerTimeout`/`chunkTimeout`) and OpenCode taking its project directory
  from `PWD` (runner now passes `--dir` and sets `PWD`).

An experiment agent was still running when this summary was written (proxy capture of OpenCode's
exact request; replay with `think:false`; a slot Modelfile with a no-think TEMPLATE; fallback to
`qwen3-coder:30b`). Its result is appended in §6 if it finished. **CONFIRM** whichever fix it
recommends before any calibration run. Every run on the R620 CPU takes 15–25 minutes, so the
GPU route (AWS G-instance quota is 0 — only you can request it: Service Quotas → EC2 → "Running
On-Demand G and VT instances" → 8) remains the way to do a real cohort.

## 4. Items reserved for you or the professor (from the consistency judge)

| # | Where | Question |
|---|---|---|
| 1 | example 01 sample | one `WRITTEN.md`/`PROCESS.md` per project (now shipped that way) — professor to confirm |
| 2 | framework §6, runbook budget | timeouts are "measured on the grading machine"; no grading machine is named yet |
| 3 | D-007 | qwen3 thinking on or off — moves every timing number; pin before seeds are issued |
| 4 | handouts §8 | "twist categories carry 35" is false for a declared all-twist program; no template says what to write |
| 5 | `docs/adr/0001` | still names five criteria and the old model (append-only record); add a banner? |
| 6 | artifact page | section numbering realigned with framework.md tonight — verify on the page |

## 5. Housekeeping you should know about

- **Ollama on this Mac** was relaunched by a student-walk agent's `ollama create` (the CLI starts the
  app). I removed the nine `ref-morris-*` slot models it created and quit the app again. `qwen3:14b`
  and `llama3` were already in your library and were left alone.
- **Docker** was never started.
- **R620 container 102** holds the rsynced repo at `/root/framework` and evidence in
  `/root/framework/evidence-cpu/`; qwen3:14b and the slot models `ref-morris-p1-q3-slot1..3` exist
  there. Nothing else on the R620 was touched.
- **Portfolio site**: branch `feat/course-ai-framework` (3 commits) — the feature as it stood,
  the 6.2 fixes, and resource-page syncs. `npm install` added `vitest`.
- **Artifacts** republished at the same URLs (framework page and student primer), label
  "Review pass 2026-09-09".
- Worktrees under `.claude/worktrees/` were used by the agents; `.claude/` is now gitignored. Prune
  with `git worktree prune` after deleting them.

## 6. Late results

**The Type B regeneration is now proven end to end on the R620 (06:00–08:30 UTC).** Root cause of
every failed run: qwen3's *thinking* mode. The model narrates its tool plan inside `<think>`,
closes the block and ends the turn with zero tool calls. Two dead ends were measured: Modelfiles
reject `PARAMETER think false`, and Ollama 0.33.3's `/v1/chat/completions` (what OpenCode uses)
silently ignores `"think": false` — three replays of OpenCode's captured request came back byte
for byte identical. The fix is a slot Modelfile whose `TEMPLATE` is the base template with two
one-line patches (always append `/no_think` to the last user message; always prefill an empty
`<think></think>` block). With it, OpenCode made nine tool calls, fetched the course page, wrote
a real 4.5 KB `MiniMaxOpening.py`, tested it with bash and **signed the ledger**
(`ABC123456  night6  127.0.0.1`). Evidence: `docs/review/evidence/cpu-run/night6-*.txt`.

Consequences applied tonight (last slice): the runner writes the patched template into every
slot Modelfile by default (`"thinking": "off"` in project.json; D-007 accepted), and the docs say
that `regeneration_timeout_s` 1200 is a GPU number — a CPU run took 28 minutes without the
course page and was still iterating at 90 minutes with it.

**CONFIRM:** the calibration run for the professor's reference specification still has to be
done on the real grading box; the R620 proves the path, not the pass rate.

**Cold TA run 6** still said "no" for both projects; every item it raised was fixed in the last
runbook slice (single-part course pre-scan, Type B ledger check after the batch, dry-run-safe
retry count, real loops for the batch commands, rehearsal note rewritten, record `tests` block
documented). A seventh run is the next check; the third student walk found the Type A path clean.

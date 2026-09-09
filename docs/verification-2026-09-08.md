# Build verification record — 2026-09-08

Machine: macOS, Python 3.14.7, Docker Desktop, Ollama installed (only `llama3` pulled), OpenCode not installed.

## Tools

| Check | Result |
|---|---|
| `ledger_server.py`: GET with `?v=` substitutes nonce/variant/base URL; POST rejects bad ID, bad nonce; accepts pair and JSON body; path traversal → 404; entries appended with header lines | pass |
| `run_tests.py`: exact-match categories, exit 1 on any failure, JSON summary | pass |
| `run_tests.py` argv-files contract against Xavier's real `MiniMaxOpening.py` (board1, depth 2 → 420 evaluations, estimate 0); a deliberately wrong expected count fails | pass |
| `combine_parts.py`: weights 45/35 → 88.75 for a fully graded row; incomplete part → incomplete | pass |
| `prescan.py`: flags override/grader/shell/URL lines; ledger `curl` to an allowed host exempted; `docker` in a hostname and `nc` as a variable name no longer false-positive | pass |
| `grade.py`: fixture with grad row, best-of-K selection, weighted categories, written scaling, milestone; arithmetic checked by hand (46.67 hidden, 15.0 written, 71.67 total) | pass |
| Sandbox image builds (`node:22-bookworm-slim` + python3 + opencode-ai 1.18.29 + iptables); runs as uid 1001 `runner` | pass (after fixing a uid collision with the base image's `node` user) |
| Firewall: `example.com` blocked (curl exit 28), `host.docker.internal` allowed; ledger POST from inside the container recorded | pass |
| `runner.py` sandboxed Type A path on example 02 and example 04 (per-variant generation) → gradebook lines identical to host runs | pass |
| `runner.py` Type B `--dry-run` on examples 01 and 03: prints 3 regenerate + 3 test commands per submission | pass |

## Examples (hidden suite, reference vs canonical)

| Example | Reference | Canonical on twist categories |
|---|---|---|
| 01 morris (B, multi-part, argv-files contract; rebuilt from the actual Project 2) | Part I: 6/6, 6/6, 4/4, grad 4/4 · Part II: 4/4, grad 2/2 | Part I opening_mill 1/6, evaluations_count 1/4 · Part II ab_pruning 0/4 |
| 02 A* (A) | 6/6, 6/6, 4/4, 8/8, 6/6, grad 4/4 | 0/8, 0/6 |
| 03 bencode (B, research pointer) | 8/8, 6/6, 6/6, 8/8, 7/7, 8/8, grad 5/5 | 0/8, 2/7, 0/8 |
| 04 scheduling (A, variants) | all pass for variants `demo` and `ABC123456` | 0/6, 0/6 |

Sample student submissions pre-scan `OK` in all four.

## Not verified

- An actual OpenCode regeneration against Ollama `qwen2.5-coder:14b`. The four items in `tools/README.md` ("Things to verify during the calibration run") remain open until someone runs the calibration checklist on a machine with the model pulled.

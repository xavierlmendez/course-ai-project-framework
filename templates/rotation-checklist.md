# Per-semester rotation checklist

Everything a returning professor changes before reusing a project.

- [ ] **Twist**: new, checked against the twist checklist. The old twist and its hidden tests are public now.
- [ ] **Published resource**: new URL path (old one 404s), new wording, new worked example.
- [ ] **Nonce**: new random string in `project.json` (`"nonce"`). The resource page reads it
      through `{{NONCE}}`, and `ledger_server.py --project` picks it up from there, so this is the
      only place it appears.
- [ ] **Hidden tests**: rewritten for the new twist; categories and weights re-checked; twist categories still sum to half.
- [ ] **Public tests**: a fresh sample, still hinting at the twist.
- [ ] **Seeds**: new `seeds.secret.json`.
- [ ] **Reference harness**: re-verify it still meets the six criteria (free, web fetch, headless, temperature, pinnable, structured tool calls). Re-run the survey if more than six months old. Re-pin the model tag, and re-run the five-attempt tool-calling probe against the pinned tag before anything else — a model that does not call tools cannot be graded with.
- [ ] **Slot models**: recreate with `--create-slots`.
- [ ] **Calibration**: full checklist again. The model may have changed; the gate must be re-passed.
- [ ] **Handout**: dates, URL, model, categories table, install guide link.
- [ ] **Ledger**: archive last semester's file; start a new one with a header line naming the semester and nonce.
- [ ] **Graduate category**: new or re-checked.

# Grill round 4 — local harness, seeds, hardware, ledger fields, calibration, rubric (2026-09-08)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Harness + model | **OpenCode + Ollama, qwen2.5-coder:14b** as this year's instance under the criteria rule. |
| Q2 | Seeds | Fixed seed per temperature slot; secret until grades released; published with the hidden tests afterward. |
| Q3 | Hardware equity | Masters-level CS students; expected to have hardware. Computer lab and an SSH-able server are available as fallback. Runner takes the Ollama server address as a parameter. |
| Q4 | Ledger entry | Fields: student ID (`^[A-Z]{3}[0-9]{6}$`), server timestamp, run tag, nonce copied from the published resource. Endpoint is write-only; file visible to professor/TAs only. Thin examples: host the published resource + ledger form as a page in Xavier's projects repo. |
| Q5 | ID during regeneration | The specification carries the sign instruction and ID; runner adds a run tag via environment. Handout states in bold that the spec must instruct the agent to sign. |
| Q6 | Calibration run | Hard rule: professor's reference specification must pass every hidden test in at least one of K regenerations before release. Reference spec doubles as the appeals answer key. |
| Q7 | Twist checklist | Included: not online; under a page; breaks canonical solution on some input class; requires course content; testable via the interface contract; hinted but not revealed by public tests. |
| Q8 | Written rubric | Accuracy, twist specificity, candor, each 0–3. Graduate adds prediction (0–3). |

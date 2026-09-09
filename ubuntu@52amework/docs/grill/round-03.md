# Grill round 3 — reference harness, ledger, safety read, temperature (2026-09-08)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Reference harness | **Local model route** (Ollama + open harness) chosen because it is reproducible: pinned weights, seed, temperature → regrading and appeals rerun identically. Framework still states the criteria any reference harness must meet; Gemini CLI documented as the free-cloud alternative. |
| Q2 | Ledger attribution | The harness **signs** the ledger entry with the student ID (format `XXXNNNNNN`: three letters, six digits). I.e. the published resource instructs the agent to write an entry; the graded behavior is that the agent followed it. |
| Q3 | Ledger hosting | Ledger is a **text file on the professor's website**, appended to from a text box + submit button (an HTML form / POST endpoint). May move to a VCS such as GitHub later. |
| Q4 | Ledger in the grade | Type A: binary gate. Type B: informational (TA runner performs the fetch). Do not try to distinguish harness fetch from manual fetch; say so in the handout. |
| Q5 | Safety read feasibility | All three: sandboxed regeneration (non-negotiable), 1,500-word cap on specifications (supporting files count), automated pre-scan flags suspicious lines for close reading. |
| Q6 | Temperature schedule | K=3 at a fixed schedule identical for every student (e.g. 0.2 / 0.6 / 1.0). |
| Q7 | Process note | Framework lists options for the professor: (A) required, ungraded; (B) it is the written component; (C) separate, lightly graded. **Default: A.** Written component stays a separate page-limited document. |
| Q8 | Type A regeneration | None. Hidden tests run once on submitted code + ledger gate. |
| Q9 | Milestone and appeals | Milestone at one-third mark: public tests pass through the reference harness, student-verified, ~10%. Appeals: one extra regeneration at the middle temperature, only if the spec passes public tests on the reference harness. |

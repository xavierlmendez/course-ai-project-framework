# Round 7 amendment — the previous project, from its actual rubric (2026-09-08)

Round 1 Q5 recorded the previous project from memory. The rubric (`Project2.pdf`, `Morris-Variant.pdf`) and Xavier's own submission and harness are now in `docs/research/prior-project-spring-2026.md`. What changed as a result:

| Area | Before | After |
|---|---|---|
| Account of the previous project | "students submitted a prompt" | Students submitted `prog.prompt` **and** `prog.py` for eight programs in four weighted parts; the rubric ran the code and checked the prompt regenerates a "functionally identical" program |
| What broke | temperature, best-of-N, model access (from memory) | Confirmed, and made precise: the rubric left model, temperature, attempt count, equivalence criterion, and the "don't edit code" rule undefined or unenforceable; positions-evaluated counts are order-dependent |
| Project types | A and B | A, B, and the **Hybrid** (code graded, specification as a reproducibility gate) documented as the previous project's shape |
| Project shape | one part | **Multi-part** supported: one directory per part, `tools/combine_parts.py` weights them |
| Interface contract | JSON stdin/stdout | Both: JSON stdin/stdout, and file-argument CLI with fixed stdout (`run_tests.py` argv-files mode, tested against Xavier's reference program) |
| Equivalence | implicit exact match or `check.py` | Named **equivalence policies** per category: `strict`, `estimate`, `ab`, `valid` |
| Twist checklist | — | Added: no order-dependent graded outputs unless the contract fixes the order; every category names its policy |
| Example 01 | invented altered board | The professor's actual Project 2 recast into the framework (Part I and Part II populated, III and IV stubbed) |
| Evidence | none | Xavier's harness: v2 prompts 60/100 → v3/v4 100/100 on `gpt-4o-mini` at temperature 0 after folding ten failure patterns into the prompts |

No settled decision from rounds 1–6 was reversed. The reference harness, best-of-K, ledger, grading arithmetic and safety controls stand.

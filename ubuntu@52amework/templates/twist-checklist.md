# Twist checklist

A twist is the deliberate deviation from the canonical problem that makes training-data recall insufficient. Tick every box before writing tests.

- [ ] **Not online in any form.** Search the exact rule and its obvious paraphrases. If a blog post, paper, or repo describes it, change it.
- [ ] **Fits in under a page** of the published resource, stated once, unambiguously, with one worked example.
- [ ] **Breaks the canonical solution** on at least one identifiable class of inputs. Write that class down; it becomes a hidden test category.
- [ ] **Requires course content to specify correctly.** A student who does not understand the underlying concept (admissibility, invariants, encoding) cannot state the twist precisely enough for a harness to implement it.
- [ ] **Testable through the interface contract alone.** No inspection of code, no interactive play, no timing beyond a per-case limit.
- [ ] **Hinted but not revealed by the public tests.** At least one public case touches the twist; none of them exhausts it.
- [ ] **Clearable by the reference harness** from your reference specification (calibration checklist). If not, simplify the twist, not the tests.
- [ ] **Has a canonical-solution failure signature** you can recognise in results: a submission that ignores the resource should score visibly low on the twist categories.
- [ ] **No graded output depends on iteration order** (a node count, a visit sequence) unless the contract fixes the order. Otherwise two correct solutions print different numbers and one of them fails.
- [ ] **Every hidden category names its equivalence policy** (`strict`, `estimate`, `ab`, `valid`) and has a `check.py` when it is not `strict`.
- [ ] **Different from last semester's.**

**The twist-half rule.** In `project.json`, the twist categories' weights sum to exactly half of the non-graduate weights; a part whose categories are all twist categories is allowed and the rule then applies trivially (all of the non-grad weight is twist, so the professor must either add a non-twist category or accept that the part is entirely twist, and say which in the handout). An all-twist part passes `scripts/review_checks.py` only when the project declares `"all_twist": true`.

## Patterns that work

- Change a movement or adjacency rule on a board or graph.
- Add a constraint the textbook algorithm's proof assumes away (negative weights, non-admissible heuristic, cyclic references in a serializer).
- Change the tie-breaking rule and test it.
- Change what counts as a terminal or winning state.

## Patterns that do not

- Renaming things (the model sees through it).
- Making the problem bigger rather than different (tests capability, not understanding).
- Hiding the twist (punishes reading, not skill, and produces appeals).

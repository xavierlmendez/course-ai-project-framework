#!/usr/bin/env python3
"""Checker: python3 check.py <in.json> <expected.json> <actual.json>
Passes (exit 0) if the actual schedule is feasible under the variant's rules and
its total equals the expected optimum. Several optimal schedules may exist, so
the chosen list is validated, not compared."""
import json
import os
import sys


def gap_of(variant):
    return 1 + sum(ord(c) for c in variant) % 4


def main():
    inp, exp, act = (json.load(open(p)) for p in sys.argv[1:4])
    variant = inp.get("variant")
    if variant is None:  # fall back to the category's variant.json
        variant = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "variant.json")))["variant"]
    g = gap_of(variant)
    if not isinstance(act, dict) or "total" not in act or "chosen" not in act:
        print("output must be an object with total and chosen"); return 1
    by_id = {j["id"]: j for j in inp["jobs"]}
    chosen = act["chosen"]
    if not isinstance(chosen, list) or len(set(map(str, chosen))) != len(chosen):
        print("chosen must be a list of unique ids"); return 1
    if any(i not in by_id for i in chosen):
        print("unknown job id in chosen"); return 1
    seq = [by_id[i] for i in chosen]
    for a, b in zip(seq, seq[1:]):
        if b["start"] < a["start"]:
            print("chosen not in start order"); return 1
        sep = 0 if b.get("class") == "P" else g
        if b["start"] < a["end"] + sep:
            print(f"infeasible: {a['id']} ends {a['end']}, {b['id']} starts {b['start']}, needs gap {sep}"); return 1
    total = sum(j["weight"] for j in seq)
    if total != act["total"]:
        print(f"total {act['total']} does not equal sum of chosen weights {total}"); return 1
    if total != exp["total"]:
        print(f"total {total} is not optimal ({exp['total']})"); return 1
    print("ok"); return 0


if __name__ == "__main__":
    sys.exit(main())

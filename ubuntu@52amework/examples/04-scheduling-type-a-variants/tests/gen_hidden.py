#!/usr/bin/env python3
"""Per-variant hidden test generator.

    python3 tests/gen_hidden.py --variant ABC123456 --out DIR [--public]

Deterministic in the variant string. Writes DIR/<category>/NNN.in.json, NNN.out.json,
check.py, variant.json. Expected outputs come from reference/solution/solve.py.
--public writes the smaller public sample (different seed, same variant) without grad_large.
"""
import argparse
import importlib.util
import json
import os
import random
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference", "solution", "solve.py")
CHECK = os.path.join(HERE, "check.py")


def load_ref():
    spec = importlib.util.spec_from_file_location("ref", REF)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def feasible(jobs_by_id, chosen, g):
    seq = [jobs_by_id[i] for i in chosen]
    for a, b in zip(seq, seq[1:]):
        sep = 0 if b.get("class") == "P" else g
        if b["start"] < a["end"] + sep:
            return False
    return True


def slotted(rng, slots, per_slot, p_frac=0.0, spacing=12):
    """Jobs in slots: every job in a slot contains the point 12s+3.5 (so in-slot jobs
    pairwise overlap) and slots are >= 5 apart (so g, at most 4, never matters)."""
    jobs, jid = [], 1
    for s in range(slots):
        for _ in range(rng.randint(*per_slot)):
            start = spacing * s + rng.randint(0, 3)
            end = spacing * s + rng.randint(4, 7)
            jobs.append({"id": f"j{jid}", "start": start, "end": end,
                         "weight": rng.randint(1, 20), "class": "P" if rng.random() < p_frac else "S"})
            jid += 1
    rng.shuffle(jobs)
    return jobs


def dense(rng, n, horizon, p_frac=0.0):
    jobs = []
    for i in range(1, n + 1):
        start = rng.randint(0, horizon)
        end = start + rng.randint(1, 6)
        jobs.append({"id": f"j{i}", "start": start, "end": end,
                     "weight": rng.randint(1, 20), "class": "P" if rng.random() < p_frac else "S"})
    rng.shuffle(jobs)
    return jobs


def make_cases(variant, ref, public):
    g = ref.gap_of(variant)
    tag = "public" if public else "hidden"
    counts = {"basic": 2 if public else 5, "overlaps": 1 if public else 5,
              "twist_cooldown": 2 if public else 6, "twist_class": 1 if public else 6,
              "grad_large": 0 if public else 4}
    out = {}
    for cat, n_cases in counts.items():
        rng = random.Random(f"{variant}:{cat}:{tag}")
        cases, tries = [], 0
        while len(cases) < n_cases and tries < 5000:
            tries += 1
            if cat == "basic":
                jobs = slotted(rng, rng.randint(2, 4), (1, 3))
            elif cat == "overlaps":
                jobs = slotted(rng, rng.randint(3, 5), (3, 5))
            elif cat == "twist_cooldown":
                jobs = dense(rng, rng.randint(6, 12), 25)
            elif cat == "twist_class":
                jobs = dense(rng, rng.randint(8, 14), 30, p_frac=0.4)
            else:
                jobs = dense(rng, 3000, 20000, p_frac=0.3)
            data = {"variant": variant, "jobs": jobs}
            twist = ref.solve(data)
            if cat in ("twist_cooldown", "twist_class", "grad_large"):
                by_id = {j["id"]: j for j in jobs}
                canon_chosen = canonical_choice(jobs)
                if feasible(by_id, canon_chosen, g):
                    continue  # canonical happens to be feasible; not a twist-revealing case
                if cat == "twist_class":
                    uniform = ref.solve({"variant": variant, "jobs": [dict(j, **{"class": "S"}) for j in jobs]})
                    if uniform["total"] == twist["total"]:
                        continue  # the P exemption did not matter
            cases.append((data, twist))
        out[cat] = cases
    return out


def canonical_choice(jobs):
    import bisect
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i]["end"], jobs[i]["start"]))
    ends = [jobs[i]["end"] for i in order]
    n = len(order)
    best, take, prev = [0] * (n + 1), [False] * (n + 1), [0] * (n + 1)
    for k in range(1, n + 1):
        j = jobs[order[k - 1]]
        p = min(bisect.bisect_right(ends, j["start"]), k - 1)
        if j["weight"] + best[p] > best[k - 1]:
            best[k], take[k], prev[k] = j["weight"] + best[p], True, p
        else:
            best[k], take[k], prev[k] = best[k - 1], False, k - 1
    chosen, k = [], n
    while k > 0:
        if take[k]:
            chosen.append(jobs[order[k - 1]]); k = prev[k]
        else:
            k -= 1
    chosen.sort(key=lambda j: j["start"])
    return [j["id"] for j in chosen]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--public", action="store_true")
    a = ap.parse_args()
    ref = load_ref()
    for cat, cases in make_cases(a.variant, ref, a.public).items():
        if not cases:
            continue
        d = os.path.join(a.out, cat)
        os.makedirs(d, exist_ok=True)
        shutil.copy(CHECK, os.path.join(d, "check.py"))
        with open(os.path.join(d, "variant.json"), "w") as fh:
            json.dump({"variant": a.variant, "g": ref.gap_of(a.variant)}, fh)
        for i, (data, expected) in enumerate(cases, 1):
            with open(os.path.join(d, f"{i:03d}.in.json"), "w") as fh:
                json.dump(data, fh)
            with open(os.path.join(d, f"{i:03d}.out.json"), "w") as fh:
                json.dump(expected, fh)
        print(f"{cat}: {len(cases)} cases (g={ref.gap_of(a.variant)})")


if __name__ == "__main__":
    main()

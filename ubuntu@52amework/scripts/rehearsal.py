#!/usr/bin/env python3
"""Grade a fixture cohort end to end and print a gradebook you can check by hand.

This is Phase 1's exit criterion. It builds a small multi-part course containing every
case the review found a defect in, grades it with the real tools, and prints both the
gradebook and the arithmetic each row should show, so a reader can compare the two
without trusting the tools.

    python3 scripts/rehearsal.py [--keep]

No Docker, no model, no network: the harness call is stubbed, because what is being
rehearsed is the bookkeeping, not the harness.
Standard library only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

CATEGORIES = {
    "basic": {"weight": 1, "policy": "strict"},
    "twist_rule": {"weight": 1, "twist": True, "policy": "strict"},
    "grad_hard": {"weight": 1, "grad_only": True, "policy": "strict"},
}

# student id -> (grad?, description, per-part hidden fractions, milestone, written dims)
COHORT = {
    "AAA111111": (0, "undergraduate, perfect", {"I": 1.0, "II": 1.0}, 1, (3, 3, 3)),
    "BBB222222": (1, "graduate, perfect including the graduate category", {"I": 1.0, "II": 1.0}, 1, (3, 3, 3, 3)),
    "CCC333333": (0, "undergraduate, twist categories failed", {"I": 0.5, "II": 0.5}, 1, (2, 1, 2)),
    "DDD444444+EEE555555": (0, "a pair, strong on part I only", {"I": 1.0, "II": 0.0}, 1, (3, 2, 3)),
    "FFF666666": (0, "milestone missed", {"I": 1.0, "II": 1.0}, 0, (3, 3, 3)),
    "GGG777777": (0, "written component never graded", {"I": 1.0, "II": 1.0}, 1, None),
    "HHH888888": (0, "environment failure on one slot, best of the rest still counts", {"I": 1.0, "II": 1.0}, 1, (3, 3, 3)),
    "III999999": (0, "appeal raised the part I grade", {"I": 0.0, "II": 1.0}, 1, (3, 3, 3)),
}


def sh(*args, **kw):
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True, **kw)
    if p.returncode != 0 and not kw.get("allow_fail"):
        print(p.stdout)
        sys.exit(f"FAILED: {' '.join(str(a) for a in args)}\n{p.stderr}")
    return p.stdout


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def write_json(path, obj):
    write(path, json.dumps(obj, indent=1))


def cases_for(fraction, n=4):
    """How many of n cases pass at this fraction."""
    return int(round(fraction * n)), n


def build(root):
    parts = ["I", "II"]
    weights = {"I": 60, "II": 40}
    write_json(os.path.join(root, "parts.json"),
               {"parts": [{"name": n, "weight": weights[n]} for n in parts]})

    for part in parts:
        pdir = os.path.join(root, f"part-{part}")
        write_json(os.path.join(pdir, "project.json"), {
            "name": f"rehearsal-{part}", "type": "B", "entry": "solve.py",
            "spec": f"SPEC-part-{part}.md", "part": part,
            "k": 3, "temperatures": [0.2, 0.6, 1.0],
            "hidden_points": 70, "milestone_points": 10, "written_points": 20,
            "categories": CATEGORIES,
        })
        for sid, (grad, _desc, fracs, _ms, _wr) in COHORT.items():
            frac = fracs[part]
            for slot in (1, 2, 3):
                # the environment-failure student loses slot 2 of part I to a broken machine
                if sid == "HHH888888" and part == "I" and slot == 2:
                    rec = {"submission": sid, "type": "B", "slot": slot, "complete": False,
                           "incomplete_reason": "environment: connection refused"}
                    write_json(os.path.join(pdir, "runs", sid, f"k{slot}.json"), rec)
                    continue
                # the appealing student scored zero on part I in grading
                use = frac
                if sid == "III999999" and part == "I":
                    use = 0.0
                p_, t_ = cases_for(use)
                cats = {"basic": {"pass": t_, "total": t_},
                        "twist_rule": {"pass": p_, "total": t_}}
                if grad:
                    cats["grad_hard"] = {"pass": p_, "total": t_}
                write_json(os.path.join(pdir, "runs", sid, f"k{slot}.json"), {
                    "submission": sid, "type": "B", "slot": slot, "complete": True,
                    "run_tag": f"grading-k{slot}",
                    "tests": {"solution_started": True, "categories": cats}})
            # the appeal record, written under its own name, raises part I back to full
            if sid == "III999999" and part == "I":
                cats = {"basic": {"pass": 4, "total": 4}, "twist_rule": {"pass": 4, "total": 4}}
                write_json(os.path.join(pdir, "runs", sid, "appeal-k2.json"), {
                    "submission": sid, "type": "B", "slot": 2, "complete": True,
                    "run_tag": "appeal-k2",
                    "tests": {"solution_started": True, "categories": cats}})

        status = ["student_id,status,grad,note"]
        for sid, (grad, desc, _f, _m, _w) in COHORT.items():
            st = "appeal" if sid == "III999999" else "graded"
            status.append(f"{sid},{st},{grad},{desc}")
        write(os.path.join(pdir, "status.csv"), "\n".join(status) + "\n")

    written = ["student_id,accuracy,twist,candor,prediction"]
    milestone = ["student_id,milestone"]
    for sid, (grad, _d, _f, ms, wr) in COHORT.items():
        milestone.append(f"{sid},{ms}")
        if wr is not None:
            dims = list(wr) + ([] if grad else [""])
            written.append(f"{sid}," + ",".join(str(x) for x in dims[:4]))
    write(os.path.join(root, "written.csv"), "\n".join(written) + "\n")
    write(os.path.join(root, "milestone.csv"), "\n".join(milestone) + "\n")
    return parts, weights


def expected(sid, weights):
    grad, desc, fracs, ms, wr = COHORT[sid]
    n_cats = 3 if grad else 2
    hidden_parts = {}
    for part, frac in fracs.items():
        use = 1.0 if (sid == "III999999" and part == "I") else frac   # the appeal restores it
        p_, t_ = cases_for(use)
        per = [1.0, p_ / t_] + ([p_ / t_] if grad else [])
        hidden_parts[part] = sum(per) / n_cats * 70
    wsum = sum(weights.values())
    hidden = sum(hidden_parts[p] * weights[p] / wsum for p in fracs)
    if wr is None:
        return None, "no written score, so no total"
    dims = len(wr)
    written = sum(wr) / (3 * dims) * 20
    return round(hidden + (10 if ms else 0) + written, 2), desc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the scratch directory")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="rehearsal-")
    try:
        parts, weights = build(root)
        books = []
        for part in parts:
            pdir = os.path.join(root, f"part-{part}")
            out = sh(sys.executable, os.path.join(TOOLS, "grade.py"),
                     "--project", os.path.join(pdir, "project.json"),
                     "--runs", os.path.join(pdir, "runs"),
                     "--status", os.path.join(pdir, "status.csv"))
            book = os.path.join(root, f"gb-{part}.csv")
            write(book, out)
            books.append(book)

        final = sh(sys.executable, os.path.join(TOOLS, "combine_parts.py"),
                   "--parts", os.path.join(root, "parts.json"),
                   "--written", os.path.join(root, "written.csv"),
                   "--milestone", os.path.join(root, "milestone.csv"), *books)

        print("=" * 78)
        print("COURSE GRADEBOOK (part I 60%, part II 40% of the hidden 70)")
        print("=" * 78)
        print(final)

        import csv as _csv
        rows = {r["student_id"]: r for r in _csv.DictReader(final.splitlines())}
        print("=" * 78)
        print("CHECK BY HAND")
        print("=" * 78)
        print(f"{'student':22} {'got':>8} {'expected':>9}  case")
        ok = True
        for sid in COHORT:
            exp, desc = expected(sid, weights)
            got = rows[sid]["total"]
            if exp is None:
                match = got == ""
                shown = "(none)"
            else:
                match = got != "" and abs(float(got) - exp) < 0.02
                shown = f"{exp:.2f}"
            ok = ok and match
            print(f"{sid:22} {got or '(none)':>8} {shown:>9}  {desc}"
                  f"{'' if match else '   <-- MISMATCH'}")
        print()
        print("Every row above is the tools' output beside arithmetic computed independently")
        print("from the fixture definition. The cohort covers: a perfect undergraduate, a")
        print("graduate on the wider denominator, a twist failure, a pair, a missed milestone,")
        print("an ungraded written component, an environment failure, and a granted appeal.")
        return 0 if ok else 1
    finally:
        if a.keep:
            print(f"\nscratch kept at {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

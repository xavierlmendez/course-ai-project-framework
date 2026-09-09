#!/usr/bin/env python3
"""Combine per-part gradebooks into one, for multi-part projects.

A multi-part project (e.g. Part I 45%, Part II 35%, Part III 10%, Part IV 10%)
is one project directory per part, each with its own project.json, tests and
runs, graded separately by grade.py. This script weights the per-part totals.

    combine_parts.py --parts parts.json gradebook_part1.csv gradebook_part2.csv ... > gradebook.csv

parts.json:  {"parts": [{"name": "I", "weight": 45}, {"name": "II", "weight": 35}, ...]}
The i-th CSV is the i-th part. Each CSV is grade.py output (columns student_id, status, total, ...).
Output columns: student_id, <part>_total..., <part>_status..., combined (out of 100), status
(graded only if every part is graded).
Standard library only.
"""
import argparse
import csv
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", required=True)
    ap.add_argument("gradebooks", nargs="+")
    a = ap.parse_args()
    parts = json.load(open(a.parts))["parts"]
    if len(parts) != len(a.gradebooks):
        sys.exit(f"{len(parts)} parts in parts.json but {len(a.gradebooks)} gradebooks given")
    wsum = sum(float(p["weight"]) for p in parts)
    books = []
    for path in a.gradebooks:
        with open(path, newline="") as fh:
            books.append({r["student_id"]: r for r in csv.DictReader(fh)})
    ids = sorted(set().union(*[set(b) for b in books]))
    names = [p["name"] for p in parts]
    w = csv.writer(sys.stdout)
    w.writerow(["student_id"] + [f"{n}_total" for n in names] + [f"{n}_status" for n in names] + ["combined", "status"])
    for sid in ids:
        totals, statuses, combined, complete = [], [], 0.0, True
        for p, b in zip(parts, books):
            r = b.get(sid)
            t = r.get("total", "") if r else ""
            s = r.get("status", "missing") if r else "missing"
            totals.append(t)
            statuses.append(s)
            if t == "" or s not in ("graded", "appeal"):
                complete = False
            else:
                combined += float(t) * float(p["weight"]) / wsum
        w.writerow([sid] + totals + statuses + [round(combined, 2) if complete else "", "graded" if complete else "incomplete"])


if __name__ == "__main__":
    main()

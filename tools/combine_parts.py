#!/usr/bin/env python3
"""Combine per-part gradebooks into one course gradebook.

A multi-part project (Part I 45%, Part II 35%, Part III 10%, Part IV 10%) is one
project directory per part, each graded on its own by grade.py. Only the
**hidden-test score** is per-part. The milestone and the written component are
course-level and are counted once, not once per part.

    combined_hidden = sum over parts of (weight_i / sum of weights) * hidden_i
    total           = combined_hidden + milestone + written

so a student who is perfect everywhere scores exactly hidden + milestone + written.

    combine_parts.py --parts parts.json --written written.csv --milestone milestone.csv \\
        gradebook_part1.csv gradebook_part2.csv ... > gradebook.csv

parts.json:    {"parts": [{"name": "I", "weight": 45}, {"name": "II", "weight": 35}, ...]}
               The i-th CSV is the i-th part.
written.csv:   student_id,accuracy,twist,candor[,prediction]   (0-3 each)
milestone.csv: student_id,milestone                            (1 or 0)

Each part gradebook is grade.py output; this reads its `hidden_score`, `status` and
`grad` columns and ignores its per-part milestone and written columns, which are
empty when grade.py is run per part.

A row is `graded` only when every part is graded and both course-level components are
present. Otherwise it is `incomplete` with no total.

Every part's non-empty `note` is carried into the combined `note`, prefixed with the part
name (`I: 1 slot(s) never completed`), because a per-part note such as "never completed" is
grade-relevant and the combined gradebook is the only file the TA reads before sending.
Standard library only.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import load_csv, written_score  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", required=True)
    ap.add_argument("--written", help="course-level written.csv")
    ap.add_argument("--milestone", help="course-level milestone.csv")
    ap.add_argument("--hidden-points", type=float, default=70.0)
    ap.add_argument("--milestone-points", type=float, default=10.0)
    ap.add_argument("--written-points", type=float, default=20.0)
    ap.add_argument("gradebooks", nargs="+")
    a = ap.parse_args()

    parts = json.load(open(a.parts))["parts"]
    if len(parts) != len(a.gradebooks):
        sys.exit(f"{len(parts)} parts in parts.json but {len(a.gradebooks)} gradebooks given.\n"
                 f"Every part named in parts.json must have been graded. If a part was not "
                 f"built or not run, remove it from parts.json and say so in the handout: "
                 f"dropping it here silently reweights the parts that remain.")
    wsum = sum(float(p["weight"]) for p in parts)
    if wsum <= 0:
        sys.exit("part weights sum to zero")

    books = []
    for path in a.gradebooks:
        with open(path, newline="") as fh:
            books.append({r["student_id"]: r for r in csv.DictReader(fh)})
    written = load_csv(a.written)
    milestone = load_csv(a.milestone)

    ids = sorted(set().union(*[set(b) for b in books]) | set(written) | set(milestone))
    names = [p["name"] for p in parts]

    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["student_id", "grad"] + [f"{n}_hidden" for n in names] + [f"{n}_status" for n in names]
               + ["hidden_score", "milestone", "written_raw", "written_score", "total", "status", "note"])

    for sid in ids:
        grad = False
        for b in books:
            r = b.get(sid)
            if r and str(r.get("grad", "0")).strip() in ("1", "true", "yes", "grad"):
                grad = True

        hiddens, statuses, combined, parts_ok = [], [], 0.0, True
        part_notes = []
        for p, b in zip(parts, books):
            r = b.get(sid)
            h = r.get("hidden_score", "") if r else ""
            s = r.get("status", "missing") if r else "missing"
            # A per-part note is grade-relevant ("1 slot(s) never completed") and is the only
            # place it is said, so it must survive into the combined gradebook rather than
            # being dropped: the readiness check on Day 2 reads this column.
            n = (r.get("note", "") if r else "").strip()
            if n:
                part_notes.append(f"{p['name']}: {n}")
            hiddens.append(h)
            statuses.append(s)
            if h == "" or s not in ("graded", "appeal"):
                parts_ok = False
            else:
                combined += float(h) * float(p["weight"]) / wsum

        hidden_score = round(combined, 2) if parts_ok else ""

        ms = milestone.get(sid, {}).get("milestone", "")
        ms_score = a.milestone_points if str(ms).strip() == "1" else (0.0 if ms != "" else "")

        wr = written.get(sid)
        if wr:
            wr_raw, wr_score = written_score(wr, grad, a.written_points, sid, a.written)
        else:
            wr_raw, wr_score = "", ""

        have_all = hidden_score != "" and ms_score != "" and wr_score != ""
        total = round(hidden_score + ms_score + wr_score, 2) if have_all else ""
        status = "graded" if have_all else "incomplete"
        pieces = list(part_notes)
        if not have_all:
            pieces.append("missing: " + ", ".join(
                n for n, ok in [("a part", parts_ok), ("milestone", ms_score != ""),
                                ("written", wr_score != "")] if not ok))
        note = "; ".join(pieces)

        w.writerow([sid, int(grad)] + hiddens + statuses
                   + [hidden_score, ms_score, wr_raw, wr_score, total, status, note])


if __name__ == "__main__":
    main()

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

Each part gradebook is grade.py output; this reads its `hidden_score`, `status`, `records`
and `grad` columns and ignores its per-part milestone and written columns, which are
empty when grade.py is run per part.

The combined gradebook carries `<part>_hidden` and `<part>_records` per part and **one**
course-level `status`. `<part>_records` is that part's count of complete records (`3`, or
`2 (1 never completed)`, or `missing` when the part has no row for the student): a fact
about the part. There is deliberately no `<part>_status`; it used to copy the course-level
status into every program, so an appeal scoped to one part read `appeal` on all eight.

A row is `graded` only when every part is graded and both course-level components are
present. Otherwise it is `incomplete` with no total.

Every part's non-empty `note` is carried into the combined `note`, prefixed with the part
name (`I: 1 slot(s) never completed`), because a per-part note such as "never completed" is
grade-relevant and the combined gradebook is the only file the TA reads before sending. A
note every part repeats identically (`pair`, an appeal note recorded against each program)
is said once without a prefix; a note about "never completed" is put first.
Standard library only.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import load_csv, written_score  # noqa: E402

INCOMPLETE_NOTE = "never completed"


def merge_notes(part_notes):
    """Combine the per-part notes into the pieces of one course-level note.

    Eight programs each carrying `pair` produced `I-opening: pair; I-game: pair; ...` — the
    same fact eight times, pushing the one note that changes a grade off the end of the
    column. A note that every part it appears in says identically is said once, without a
    part prefix, because it is a property of the submission and not of a part. A note only
    some parts say keeps its part prefix, because which part it is about is the point.
    `never completed` is ordered first whatever else is in the row: it is the note the
    readiness check on Day 2 is looking for.
    """
    order = {}
    for name, note in part_notes:
        order.setdefault(note, []).append(name)
    pieces = [(note if len(names) > 1 else f"{names[0]}: {note}", INCOMPLETE_NOTE in note)
              for note, names in order.items()]
    pieces.sort(key=lambda p: not p[1])          # stable: incompletes first, else part order
    return [text for text, _first in pieces]


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
    w.writerow(["student_id", "grad"] + [f"{n}_hidden" for n in names] + [f"{n}_records" for n in names]
               + ["hidden_score", "milestone", "written_raw", "written_score", "total", "status", "note"])

    for sid in ids:
        grad = False
        for b in books:
            r = b.get(sid)
            if r and str(r.get("grad", "0")).strip() in ("1", "true", "yes", "grad"):
                grad = True

        hiddens, records, combined, parts_ok = [], [], 0.0, True
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
                part_notes.append((p["name"], n))
            hiddens.append(h)
            # What the part contributed, as evidence rather than as a status: the number of
            # complete records it was scored from, and the incomplete ones in brackets. The
            # old `<part>_status` column copied the course-level status into all eight
            # programs, so an appeal scoped to one part read `appeal` on every one of them.
            records.append(r.get("records", "") if r else "missing")
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
        pieces = merge_notes(part_notes)
        if not have_all:
            pieces.append("missing: " + ", ".join(
                n for n, ok in [("a part", parts_ok), ("milestone", ms_score != ""),
                                ("written", wr_score != "")] if not ok))
        note = "; ".join(pieces)

        w.writerow([sid, int(grad)] + hiddens + records
                   + [hidden_score, ms_score, wr_raw, wr_score, total, status, note])


if __name__ == "__main__":
    main()

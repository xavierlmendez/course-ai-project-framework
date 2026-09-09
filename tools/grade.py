#!/usr/bin/env python3
"""Aggregate runner records into a gradebook. Standard library only.

    grade.py --project project.json --runs runs/ [--status status.csv]
             [--written written.csv] [--milestone milestone.csv] > gradebook.csv

Hidden score (out of hidden_points, default 70):
    sum over applicable categories of weight_c * pass_c / total_c,
    normalised by the sum of applicable weights.
Applicable = all categories for graduate rows; non-grad_only for others.
Type B: score of the best of the K runs. Type A: the single run.

written.csv:   student_id,accuracy,twist,candor[,prediction]   (0-3 each; a value outside
               that range is an error, not a silent clamp)
milestone.csv: student_id,milestone                         (1 or 0)
status.csv:    student_id,status,grad,note                  (`grad` is required: 1 for a
               graduate row, 0 otherwise. A file without the column is rejected, because
               defaulting it silently grades every graduate on the undergraduate bar.)

A row is only `graded` when every component it needs is present. A missing written or
milestone row makes the row `incomplete` with no total, rather than a total that silently
omits 30 of the 100 points.
"""
import argparse
import csv
import glob
import json
import os
import sys


def load_csv(path, key="student_id", require=()):
    if not path or not os.path.exists(path):
        return {}
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        cols = set(rd.fieldnames or [])
        missing = [c for c in require if c not in cols]
        if missing:
            sys.exit(f"{path}: missing required column(s) {', '.join(missing)}. "
                     f"Found: {', '.join(sorted(cols)) or '(none)'}")
        return {r[key]: r for r in rd}


DIMENSION_MAX = 3


def written_score(row, grad, written_pts, sid, path):
    """Return (raw, scaled). Refuses any dimension outside 0..DIMENSION_MAX."""
    dims = ["accuracy", "twist", "candor"] + (["prediction"] if grad else [])
    raw = 0.0
    for d in dims:
        v = row.get(d, "")
        if v is None or str(v).strip() == "":
            sys.exit(f"{path}: {sid} has no value for written dimension '{d}'")
        try:
            x = float(v)
        except ValueError:
            sys.exit(f"{path}: {sid} written dimension '{d}' is not a number: {v!r}")
        if x < 0 or x > DIMENSION_MAX:
            sys.exit(f"{path}: {sid} written dimension '{d}' is {x}, outside 0..{DIMENSION_MAX}")
        raw += x
    return raw, round(raw / (DIMENSION_MAX * len(dims)) * written_pts, 2)


def category_scores(tests, cats, grad):
    """Return (score_fraction, {cat: (pass,total)})."""
    if not tests or not tests.get("solution_started", False) and not tests.get("categories"):
        return 0.0, {}
    detail, num, den = {}, 0.0, 0.0
    for name, meta in cats.items():
        if meta.get("grad_only") and not grad:
            continue
        w = float(meta.get("weight", 1))
        c = tests.get("categories", {}).get(name, {"pass": 0, "total": 0})
        p, t = c.get("pass", 0), c.get("total", 0)
        detail[name] = (p, t)
        if not t:
            # A category with no cases carries no information. Counting its weight in the
            # denominator would cap every student below full marks for a category that was
            # declared but never written.
            continue
        num += w * p / t
        den += w
    return (num / den if den else 0.0), detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--status")
    ap.add_argument("--written")
    ap.add_argument("--milestone")
    ap.add_argument("--hidden-only", action="store_true",
                    help="grade one part of a multi-part project: emit the hidden score only. "
                         "Implied when project.json declares a `part`. The milestone and the "
                         "written component are course-level and are added once by combine_parts.py.")
    a = ap.parse_args()

    p = json.load(open(a.project))
    cats = p["categories"]
    hidden_only = a.hidden_only or bool(p.get("part"))
    hidden_pts = float(p.get("hidden_points", 70))
    milestone_pts = float(p.get("milestone_points", 10))
    written_pts = float(p.get("written_points", 20))
    status = load_csv(a.status, require=("status", "grad"))
    written = load_csv(a.written)
    milestone = load_csv(a.milestone)

    if not os.path.isdir(a.runs):
        sys.exit(f"runs directory not found: {a.runs}\n"
                 f"For a multi-part project, each part has its own runs/ directory. A part "
                 f"that was never run has none, and it cannot be graded or combined.")
    cat_names = list(cats)
    header = ["student_id", "status", "grad", "best_slot", "hidden_score"] + \
             [f"{c}_pass" for c in cat_names] + ["milestone", "written_raw", "written_score", "total", "note"]
    # \n, not csv's default \r\n: the carriage returns broke every downstream text check.
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(header)

    ids = sorted(set(os.listdir(a.runs)) | set(status))
    for sid in ids:
        st = status.get(sid, {"status": "graded", "grad": "0", "note": ""})
        grad = str(st.get("grad", "0")).strip() in ("1", "true", "yes", "grad")
        recs, all_recs = [], []
        for f in sorted(glob.glob(os.path.join(a.runs, sid, "*.json"))):
            if f.endswith(".dry.json"):
                continue          # a --dry-run record is a printed command line, not a run
            try:
                r = json.load(open(f))
            except Exception:
                continue
            all_recs.append(r)
            if r.get("complete"):
                recs.append(r)
        best, best_frac, best_detail = None, -1.0, {}
        for r in recs:
            frac, detail = category_scores(r.get("tests"), cats, grad)
            if frac > best_frac:
                best, best_frac, best_detail = r, frac, detail
        hidden = round(max(best_frac, 0.0) * hidden_pts, 2) if best else ""
        best_slot = (best.get("slot") if best and best.get("type") == "B" else ("A" if best else ""))
        ms = milestone.get(sid, {}).get("milestone", "")
        ms_score = milestone_pts if str(ms).strip() == "1" else (0.0 if ms != "" else "")
        wr = written.get(sid)
        if wr:
            wr_raw, wr_score = written_score(wr, grad, written_pts, sid, a.written)
        else:
            wr_raw, wr_score = "", ""
        eligible = st.get("status") in ("graded", "appeal")
        if hidden_only:
            # A part contributes its hidden score and nothing else; completeness of the
            # course-level components is combine_parts.py's job.
            have_all = hidden != ""
            total = ""
        else:
            have_all = hidden != "" and ms_score != "" and wr_score != ""
            total = round(hidden + ms_score + wr_score, 2) if eligible and have_all else ""
        out_status = st.get("status", "")
        note = st.get("note", "")
        if eligible and not have_all:
            out_status = "incomplete"
            why = [n for n, ok in (("hidden", hidden != ""), ("milestone", ms_score != ""),
                                   ("written", wr_score != "")) if not ok]
            note = ("missing: " + ", ".join(why) + ("; " + note if note else "")) if why else note
        incomplete_slots = sum(1 for r in all_recs if not r.get("complete"))
        if incomplete_slots:
            note = (note + "; " if note else "") + f"{incomplete_slots} slot(s) never completed"
        row = [sid, out_status, int(grad), best_slot, hidden]
        row += [f"{best_detail[c][0]}/{best_detail[c][1]}" if c in best_detail else "" for c in cat_names]
        row += [ms_score, wr_raw, wr_score, total, note]
        w.writerow(row)


if __name__ == "__main__":
    main()

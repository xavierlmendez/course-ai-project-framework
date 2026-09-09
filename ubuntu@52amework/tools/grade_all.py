#!/usr/bin/env python3
"""Grade a whole project, single-part or multi-part, in one command.

    grade_all.py --project DIR --status status.csv \\
                 [--submissions submissions/] \\
                 [--written written.csv] [--milestone milestone.csv] > gradebook.csv

`DIR` is the project directory. If it contains `parts.json` the project is multi-part:
each part is graded on its own (hidden score only) and the results are combined once,
with the milestone and written component added at the course level. Otherwise `DIR` is
graded directly.

`--submissions` is the course-level submission tree, in the layout the handout asks
students for. Given it, `fan_out.py` runs first, so the per-program submission directories
the grading reads are refreshed from what the students actually submitted, and a layout
problem stops the run rather than becoming a silent zero for a mislaid program.

This exists because the equivalent shell loop was a reliable source of mistakes: it
word-splits differently in bash and zsh, it silently continues past a part that was never
run, and dropping an ungraded part from the combine step quietly reweights the parts that
remain. Here, a part that cannot be graded stops the run and says so.
Standard library only.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, out_path=None):
    if out_path:
        with open(out_path, "wb") as fh:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE)
    else:
        r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write((r.stderr or b"").decode(errors="replace"))
        sys.exit(f"\nfailed: {' '.join(cmd)}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="the project directory")
    ap.add_argument("--status", required=True)
    ap.add_argument("--written")
    ap.add_argument("--milestone")
    ap.add_argument("--work", help="where to put per-part gradebooks (default: alongside the project)")
    ap.add_argument("--submissions",
                    help="the course-level submissions directory (one directory per student, in "
                         "the handout's layout). Given this, the fan-out runs first and the "
                         "grading stops if any student's layout is wrong.")
    a = ap.parse_args()

    pdir = os.path.abspath(a.project)
    parts_file = os.path.join(pdir, "parts.json")

    if a.submissions:
        if not os.path.exists(parts_file):
            sys.exit(f"--submissions is the course-level tree of a multi-part project, but "
                     f"{parts_file} does not exist. A single-part project is graded from its "
                     f"own submissions directory by the runner; there is nothing to fan out.")
        sys.path.insert(0, HERE)
        import fan_out
        bad = fan_out.fan_out(pdir, os.path.abspath(a.submissions), out=sys.stderr)
        if bad:
            sys.exit(f"\n{len(bad)} student submission(s) do not match the handout's layout "
                     f"(listed above). Grading now would score a mislaid program as a zero, so "
                     f"fix the layout or accept it deliberately, then run the fan-out again:\n"
                     f"  python3 tools/fan_out.py --project {a.project} "
                     f"--submissions {a.submissions}")
    work = a.work or pdir
    os.makedirs(work, exist_ok=True)

    if not os.path.exists(parts_file):
        cmd = [sys.executable, os.path.join(HERE, "grade.py"),
               "--project", os.path.join(pdir, "project.json"),
               "--runs", os.path.join(pdir, "runs"), "--status", a.status]
        if a.written:
            cmd += ["--written", a.written]
        if a.milestone:
            cmd += ["--milestone", a.milestone]
        r = run(cmd)
        sys.stdout.write(r.stdout.decode())
        return 0

    parts = json.load(open(parts_file))["parts"]
    missing = []
    for p in parts:
        d = os.path.join(pdir, f"part-{p['name']}")
        if not os.path.isdir(os.path.join(d, "runs")):
            missing.append(p["name"])
    if missing:
        sys.exit(
            f"parts.json lists {', '.join(p['name'] for p in parts)}, but "
            f"part{'s' if len(missing) > 1 else ''} {', '.join(missing)} "
            f"{'have' if len(missing) > 1 else 'has'} no runs/ directory.\n"
            "Every part named in parts.json must have been graded before the results can be\n"
            "combined. Removing a part from parts.json to get past this reweights the parts\n"
            "that remain, so it is the professor's decision, not yours.")

    books = []
    for p in parts:
        d = os.path.join(pdir, f"part-{p['name']}")
        book = os.path.join(work, f"gb-{p['name']}.csv")
        run([sys.executable, os.path.join(HERE, "grade.py"),
             "--project", os.path.join(d, "project.json"),
             "--runs", os.path.join(d, "runs"),
             "--status", a.status, "--hidden-only"], out_path=book)
        books.append(book)
        sys.stderr.write(f"graded part {p['name']} -> {book}\n")

    cmd = [sys.executable, os.path.join(HERE, "combine_parts.py"), "--parts", parts_file]
    if a.written:
        cmd += ["--written", a.written]
    if a.milestone:
        cmd += ["--milestone", a.milestone]
    r = run(cmd + books)
    sys.stdout.write(r.stdout.decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())

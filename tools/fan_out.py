#!/usr/bin/env python3
"""Fan a course-level submission tree out into the per-program directories the tools grade.

Students submit **one directory each**, laid out the way the handout tells them (§6):

    submissions/ABC123456/
        part-I-opening/SPEC.md      one sub-directory per program, named as the program
        part-I-game/SPEC.md         directories are: part-<name> for every name in parts.json
        ...
        WRITTEN.md                  one page for the whole project
        PROCESS.md                  one page for the whole project

The grading tools work per program: `runner.py --submissions part-I-opening/submissions/`
wants `<submission>/SPEC.md` at the top level, and `prescan.py` scans one such directory.
Nothing bridged the two, so a TA had to move eight sets of files by hand and could not tell
a student who skipped a program from one whose files were mislaid. This is that bridge.

    fan_out.py --project examples/01-morris-type-b --submissions .../submissions [--check]

For every student directory it verifies the layout, then writes

    <course>/part-<program>/submissions/<id>/
        SPEC.md        the program's own specification
        WRITTEN.md     copied from the top level, so the per-program prescan still sees it
        PROCESS.md     likewise
        <other files>  the files beside that SPEC.md, including any the part declares in
                       `data_files`; the runner carries the ones the specification names

A program the student never submitted still gets a directory, holding a `MISSING.txt` note
instead of a specification: the runner then skips it as having no specification and the
gradebook shows the program unscored with that reason, which is right and is visible.

`part-<program>/submissions/<id>/` is this tool's output and nothing else's. Re-running
refreshes it in place, so the fan-out can be repeated after a resubmission, and a file that
is no longer in the submission disappears from it. It refuses to touch a destination that
holds a `runs/` directory, because that is grading evidence and not this tool's to overwrite.

Exit 1 if any student had a layout problem, but only after every student is processed: a TA
wants the whole list in one pass, not the first bad name.
Standard library only.
"""
import argparse
import json
import os
import shutil
import sys

PAGES = ("WRITTEN.md", "PROCESS.md")
MISSING_NOTE = """This program was not part of the submission.

The student's course-level submission directory had no {spec} under `{dirname}/`,
so there is nothing to regenerate. The runner will skip this submission as having no
specification, and the gradebook will show the program unscored with that reason.

Written by tools/fan_out.py. Delete this file only after putting a real {spec} beside
it and re-running the fan-out.
"""


def part_dir(project_dir, name):
    return os.path.join(project_dir, f"part-{name}")


def load_parts(project_dir):
    """[(name, student sub-directory name, spec file, [declared data files])], parts.json order."""
    parts_file = os.path.join(project_dir, "parts.json")
    if not os.path.exists(parts_file):
        sys.exit(f"{parts_file} not found. --project must be the course directory holding "
                 "parts.json; a single-part project has no course-level tree to fan out.")
    try:
        parts = json.load(open(parts_file))["parts"]
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"{parts_file}: {e}")
    out = []
    for part in parts:
        name = part["name"]
        cfg = {}
        pj = os.path.join(part_dir(project_dir, name), "project.json")
        if os.path.exists(pj):
            try:
                cfg = json.load(open(pj))
            except (OSError, ValueError):
                cfg = {}
        spec = part.get("spec") or cfg.get("spec") or "SPEC.md"
        data = list(part.get("data_files") or cfg.get("data_files") or [])
        out.append((name, f"part-{name}", spec, data))
    return out


def inspect(student_dir, programs):
    """(problems, {program: spec words}, [missing programs]) for one student directory.

    A problem is a layout fault the student must be told about. Extra *files* beside a
    SPEC.md are not faults: the handout allows supporting files, and the runner decides
    which of them to carry by whether the specification names them.
    """
    problems, words, missing = [], {}, []
    dirnames = [d for _n, d, _s, _f in programs]
    for entry in sorted(os.listdir(student_dir)):
        if entry.startswith("."):
            continue
        p = os.path.join(student_dir, entry)
        if os.path.isdir(p):
            if entry not in dirnames:
                problems.append(f"unknown-directory:{entry}")
        elif entry not in PAGES:
            problems.append(f"stray-file:{entry}")
    for page in PAGES:
        if not os.path.isfile(os.path.join(student_dir, page)):
            problems.append(f"missing:{page}")
    for name, dirname, spec, data in programs:
        d = os.path.join(student_dir, dirname)
        sp = os.path.join(d, spec)
        if not os.path.isfile(sp):
            missing.append(name)
            problems.append(f"missing-program:{dirname}" if not os.path.isdir(d)
                            else f"missing:{dirname}/{spec}")
            continue
        words[name] = len(open(sp, encoding="utf-8", errors="replace").read().split())
        for entry in sorted(os.listdir(d)):
            if entry.startswith("."):
                continue
            if os.path.isdir(os.path.join(d, entry)):
                problems.append(f"unknown-directory:{dirname}/{entry}")
        for df in data:
            if not os.path.isfile(os.path.join(d, df)):
                problems.append(f"missing:{dirname}/{df}")
    return problems, words, missing


def place(project_dir, sid, student_dir, programs, missing):
    """Write the per-program copies. Returns problems found while writing."""
    problems = []
    for name, dirname, spec, _data in programs:
        dest = os.path.join(part_dir(project_dir, name), "submissions", sid)
        if os.path.isdir(os.path.join(dest, "runs")):
            problems.append(f"has-runs:part-{name}/submissions/{sid}/runs")
            continue
        os.makedirs(dest, exist_ok=True)
        written = set()
        if name in missing:
            with open(os.path.join(dest, "MISSING.txt"), "w", encoding="utf-8") as fh:
                fh.write(MISSING_NOTE.format(spec=spec, dirname=dirname))
            written.add("MISSING.txt")
        else:
            src_dir = os.path.join(student_dir, dirname)
            for f in sorted(os.listdir(src_dir)):
                if f.startswith(".") or not os.path.isfile(os.path.join(src_dir, f)):
                    continue
                shutil.copyfile(os.path.join(src_dir, f), os.path.join(dest, f))
                written.add(f)
            for page in PAGES:
                src = os.path.join(student_dir, page)
                if os.path.isfile(src):
                    shutil.copyfile(src, os.path.join(dest, page))
                    written.add(page)
        # This directory is the fan-out's output. A file in it that this pass did not write
        # is from an earlier submission and must go, or the harness would receive a file the
        # student has withdrawn. Directories are left alone; runs/ was refused above.
        for f in sorted(os.listdir(dest)):
            p = os.path.join(dest, f)
            if os.path.isfile(p) and f not in written:
                os.remove(p)
    return problems


def students(submissions_dir):
    if not os.path.isdir(submissions_dir):
        sys.exit(f"--submissions {submissions_dir} is not a directory")
    return [d for d in sorted(os.listdir(submissions_dir))
            if os.path.isdir(os.path.join(submissions_dir, d)) and not d.startswith(".")]


def summary(rows, bad, programs, out=sys.stdout):
    names = [n for n, _d, _s, _f in programs]
    width = max([len(sid) for sid, _w, _m in rows] + [len("student")])
    print("programs, in parts.json order: " + " ".join(names), file=out)
    print(f"{'student':<{width}}  present  words per program", file=out)
    for sid, words, _missing in rows:
        cells = " ".join(f"{words.get(n, '-'):>7}" for n in names)
        present = f"{len(words)}/{len(names)}"
        print(f"{sid:<{width}}  {present:>7}  {cells}", file=out)
    if bad:
        print("\nlayout problems:", file=out)
        for sid in sorted(bad):
            print(f"  {sid}: {' '.join(bad[sid])}", file=out)
    else:
        print("\nevery student directory matches the handout's layout.", file=out)


def fan_out(project_dir, submissions_dir, check=False, out=sys.stdout):
    """Verify and, unless check, place. Returns {student id: [problems]}; empty when clean."""
    programs = load_parts(project_dir)
    rows, bad = [], {}
    for sid in students(submissions_dir):
        sdir = os.path.join(submissions_dir, sid)
        problems, words, missing = inspect(sdir, programs)
        if not check:
            problems += place(project_dir, sid, sdir, programs, missing)
        if problems:
            bad[sid] = problems
        rows.append((sid, words, missing))
    if rows:
        summary(rows, bad, programs, out)
    else:
        print(f"no student directories under {submissions_dir}", file=out)
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, help="the course directory holding parts.json")
    ap.add_argument("--submissions", required=True,
                    help="the course-level submissions directory, one sub-directory per student")
    ap.add_argument("--check", action="store_true",
                    help="validate the layout and print the table; write nothing")
    a = ap.parse_args(argv)
    bad = fan_out(os.path.abspath(a.project), os.path.abspath(a.submissions), check=a.check)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

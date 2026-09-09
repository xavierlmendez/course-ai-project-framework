#!/usr/bin/env python3
"""The milestone: evidence that a student got the reference setup working.

Two subcommands.

    milestone.py record --project project.json --solution DIR --student-id ABC123456 \\
                        [--regeneration runs/<id>/practice-k1.json] --out milestone.json

        Run by the **student**. Runs the public suite against a solution directory and
        writes a record naming the student, the project, the harness and model that
        produced it, and the public-suite result.

        **Type A**: `--solution` is the directory holding the code you are submitting.

        **Type B**: you do not write the code, so `--solution` is the directory the harness
        wrote for you. Do a practice run first, then point at its working directory:

            python3 tools/runner.py --project project.json --submission ./my-submission \\
                    --run-tag practice --slot 1 --out ./practice --no-sandbox
            python3 tools/milestone.py record --project project.json \\
                    --solution ./practice/my-submission/practice-k1-work \\
                    --regeneration ./practice/my-submission/practice-k1.json \\
                    --student-id ABC123456 --out milestone.json

        The point of the milestone is that this whole path worked on your machine.

    milestone.py check --project project.json --records DIR --status status.csv > milestone.csv

        Run by a **TA**. Validates every submitted record and writes the milestone.csv
        that grade.py reads. A record passes when its digest matches, it names this
        project, its student is on the roster, and every public test passed.

        Records are matched to `status.csv` rows on any **shared member**, so a pair's
        record may name either partner or the pair in any of its forms (`A+B`, `A-B`,
        `A,B`). The output has exactly one row per `status.csv` row.

What the digest is and is not: it makes casual editing of a record detectable, so a
student cannot change a failing run into a passing one by opening the file. It is not a
signature and does not prove the run happened, because the student controls the machine.
The ledger entry is the independent evidence; submitting a fabricated record is
misconduct like any other fabricated artifact.
Standard library only.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIGEST_KEY = "digest"


def members(key):
    """A roster key, a ledger pair or a submission directory name, split into student ids.
    Pairs are written `A+B` in the ledger, `A-B` as a directory, `A,B` in a roster, so the
    three forms name the same pair. Mirrors `members()` in runner.py's `roster_variant`."""
    out = []
    for part in re.split(r"[+,\-]", key or ""):
        part = part.strip().upper()
        if part:
            out.append(part)
    return out


def same_student(a, b):
    """True when two ids name the same student or the same pair, in any of the forms.
    A shared member is enough: a pair's record may name either partner."""
    x, y = set(members(a)), set(members(b))
    return bool(x and y and (x == y or x & y))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def digest_of(record):
    body = {k: v for k, v in record.items() if k != DIGEST_KEY}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def run_public_suite(p, project_dir, solution, timeout):
    tests = os.path.join(project_dir, p.get("public_tests", "tests/public"))
    if not os.path.isdir(tests):
        sys.exit(f"public tests not found at {tests}")
    cmd = [sys.executable, os.path.join(HERE, "run_tests.py"),
           "--solution", solution, "--tests", tests,
           "--entry", p.get("entry", "solve.py"), "--timeout", str(timeout), "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        sys.exit(f"could not read the public-suite result:\n{r.stderr[-1500:]}")


def cmd_record(a):
    p = json.load(open(a.project))
    project_dir = os.path.dirname(os.path.abspath(a.project))
    summary = run_public_suite(p, project_dir, a.solution, p.get("test_timeout_s", 10))
    cats = summary.get("categories", {})
    passed = sum(c["pass"] for c in cats.values())
    total = sum(c["total"] for c in cats.values())

    harness = {"model": p.get("base_model")}
    if a.regeneration and os.path.exists(a.regeneration):
        reg = json.load(open(a.regeneration))
        harness["harness_exit"] = reg.get("regeneration", {}).get("harness_exit")
        harness["wall_s"] = reg.get("regeneration", {}).get("wall_s")
        harness["run_tag"] = reg.get("run_tag")
    # A pair may type their id in any of the accepted forms (`A+B`, `A-B`, `A,B`, or one
    # partner alone). Normalise to the ledger's `A+B` so the record is self-consistent;
    # `check` matches it to the roster on any shared member either way.
    ids = members(a.student_id)
    rec = {
        "student_id": "+".join(ids) if ids else a.student_id.strip().upper(),
        "project": p.get("name"),
        "part": p.get("part"),
        "type": p.get("type", "B"),
        "harness": harness,
        "public": {"pass": passed, "total": total,
                   "categories": {k: {"pass": v["pass"], "total": v["total"]} for k, v in cats.items()},
                   "solution_started": summary.get("solution_started", False)},
        "generated": now(),
    }
    rec[DIGEST_KEY] = digest_of(rec)
    with open(a.out, "w") as fh:
        json.dump(rec, fh, indent=1)
    state = "PASS" if total and passed == total else "FAIL"
    print(f"{state}: public suite {passed}/{total}. Wrote {a.out}")
    print("Submit that file. Keep working until it says PASS." if state == "FAIL" else "Submit that file.")
    return 0 if state == "PASS" else 1


def validate(rec, p):
    """Return a list of reasons the record is not acceptable."""
    bad = []
    if not isinstance(rec, dict):
        return ["not a JSON object"]
    if DIGEST_KEY not in rec:
        bad.append("no digest")
    elif rec[DIGEST_KEY] != digest_of(rec):
        bad.append("digest does not match the contents (edited after it was written)")
    if rec.get("project") != p.get("name"):
        bad.append(f"record is for project {rec.get('project')!r}, not {p.get('name')!r}")
    if p.get("part") and rec.get("part") != p.get("part"):
        bad.append(f"record is for part {rec.get('part')!r}, not {p.get('part')!r}")
    pub = rec.get("public") or {}
    if not pub.get("total"):
        bad.append("no public tests were run")
    elif pub.get("pass") != pub.get("total"):
        bad.append(f"public suite {pub.get('pass')}/{pub.get('total')}")
    return bad


def cmd_check(a):
    p = json.load(open(a.project))
    # The roster keys, in status.csv order and de-duplicated. The output has exactly one row
    # per status.csv row, so a pair never produces a phantom second row under a partner's id.
    roster = []
    if a.status and os.path.exists(a.status):
        with open(a.status, newline="") as fh:
            for r in csv.DictReader(fh):
                key = (r.get("student_id") or "").strip()
                if key and key not in roster:
                    roster.append(key)

    def roster_key(sid):
        """The status.csv key this record belongs to, matching on any shared member."""
        for key in roster:
            if same_student(sid, key):
                return key
        return None

    results = {}
    for name in sorted(os.listdir(a.records)):
        path = os.path.join(a.records, name)
        if not os.path.isfile(path) or not name.endswith(".json"):
            continue
        try:
            rec = json.load(open(path))
        except Exception as e:
            print(f"{name}: unreadable ({e})", file=sys.stderr)
            continue
        sid = (rec.get("student_id") or os.path.splitext(name)[0]).strip().upper()
        reasons = validate(rec, p)
        key = roster_key(sid) if roster else sid
        if roster and key is None:
            # Not one of the graded submissions: report it, but do not invent a row.
            print(f"{sid}: not on the roster", file=sys.stderr)
            continue
        # A pair may submit one record per partner. One acceptable record earns the
        # milestone for the pair, so a passing record replaces a failing one.
        if key not in results or (results[key] and not reasons):
            results[key] = reasons
        if reasons:
            print(f"{sid}: {'; '.join(reasons)}", file=sys.stderr)

    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["student_id", "milestone", "note"])
    ids = roster if roster else sorted(results)
    for sid in ids:
        if sid not in results:
            w.writerow([sid, 0, "no milestone record submitted"])
        else:
            reasons = results[sid]
            w.writerow([sid, 0 if reasons else 1, "; ".join(reasons)])
    passed = sum(1 for sid in ids if sid in results and not results[sid])
    print(f"{passed} of {len(ids)} passed the milestone", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="student: run the public suite and write a record")
    r.add_argument("--project", required=True)
    r.add_argument("--solution", required=True, help="directory holding the entry point")
    r.add_argument("--student-id", required=True)
    r.add_argument("--regeneration", help="the runner's practice record, for Type B")
    r.add_argument("--out", default="milestone.json")
    r.set_defaults(fn=cmd_record)

    c = sub.add_parser("check", help="TA: validate submitted records into milestone.csv")
    c.add_argument("--project", required=True)
    c.add_argument("--records", required=True, help="directory of submitted milestone records")
    c.add_argument("--status", help="status.csv, to catch records from students not on the roster")
    c.set_defaults(fn=cmd_check)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

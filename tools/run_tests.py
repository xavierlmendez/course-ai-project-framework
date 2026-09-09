#!/usr/bin/env python3
"""Run interface-contract tests against a solution directory.

Test layout (either flat or one subdirectory per category):

  stdio contract (default):
    tests/<category>/<name>.in.json     stdin for the solution
    tests/<category>/<name>.out.json    expected stdout (exact JSON equality) ...
    tests/<category>/check.py           ... or, if present, a checker:
                                        python3 check.py <in.json> <out.json> <actual.json>
                                        exit 0 = pass, anything else = fail

  argv-files contract (a case is detected by the presence of <name>.args):
    tests/<category>/<name>.args        one line of arguments; {in} and {out} are replaced by
                                        temp paths holding <name>.in.txt and the output file
    tests/<category>/<name>.in.txt      content of the input file
    tests/<category>/<name>.stdout.txt  expected stdout (compared line by line, trailing
                                        whitespace ignored) ...
    tests/<category>/<name>.outfile.txt expected content of the output file (optional)
    tests/<category>/check.py           ... or a checker: python3 check.py <in.txt> <name>.stdout.txt
                                        <actual.json>, where actual.json = {"stdout": ..., "outfile": ...}

Contract (stdio): the entry point reads one JSON object on stdin and writes one
JSON object on stdout. Contract (argv-files): the entry point is run as
`python3 <entry> <args>`, e.g. `python3 MiniMaxOpening.py {in} {out} 3`.

Usage:
    run_tests.py --solution DIR --tests DIR [--entry solve.py] [--timeout 10]
                 [--python python3] [--json]
Standard library only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time


def discover(tests_dir):
    """Return {category: [(name, in_path, out_path, checker_or_None, mode)]}.
    mode is "stdio" or "argv"."""
    cats = {}
    entries = sorted(os.listdir(tests_dir))
    subdirs = [e for e in entries if os.path.isdir(os.path.join(tests_dir, e))]
    targets = [(d, os.path.join(tests_dir, d)) for d in subdirs] or [("all", tests_dir)]
    for cat, path in targets:
        checker = os.path.join(path, "check.py")
        checker = checker if os.path.exists(checker) else None
        cases = []
        for f in sorted(os.listdir(path)):
            if f.endswith(".in.json"):
                name = f[: -len(".in.json")]
                out = os.path.join(path, name + ".out.json")
                cases.append((name, os.path.join(path, f), out if os.path.exists(out) else None, checker, "stdio"))
            elif f.endswith(".args"):
                name = f[: -len(".args")]
                out = os.path.join(path, name + ".stdout.txt")
                cases.append((name, os.path.join(path, name + ".in.txt"), out if os.path.exists(out) else None, checker, "argv"))
        if cases:
            cats[cat] = cases
    return cats


def run_case_argv(solution, entry, python, in_path, args_path, timeout):
    """argv-files contract: python3 entry <args with {in}/{out} substituted>."""
    tmp = tempfile.mkdtemp(prefix="case-")
    in_tmp = os.path.join(tmp, "input.txt")
    out_tmp = os.path.join(tmp, "output.txt")
    shutil.copyfile(in_path, in_tmp)
    args = open(args_path).read().strip().replace("{in}", in_tmp).replace("{out}", out_tmp).split()
    t0 = time.time()
    try:
        p = subprocess.run([python, entry] + args, cwd=solution, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmp, ignore_errors=True)
        return {"status": "timeout", "wall_s": round(time.time() - t0, 3)}
    except FileNotFoundError as e:
        shutil.rmtree(tmp, ignore_errors=True)
        return {"status": "no_entry", "error": str(e), "wall_s": 0}
    wall = round(time.time() - t0, 3)
    outfile = open(out_tmp, encoding="utf-8", errors="replace").read() if os.path.exists(out_tmp) else None
    shutil.rmtree(tmp, ignore_errors=True)
    if p.returncode != 0:
        return {"status": "crash", "returncode": p.returncode,
                "stderr": p.stderr.decode(errors="replace")[-2000:], "wall_s": wall}
    return {"status": "ok", "actual": {"stdout": p.stdout.decode(errors="replace"), "outfile": outfile}, "wall_s": wall}


def norm_lines(text):
    return [l.rstrip() for l in (text or "").strip().splitlines()]


def judge_argv(result, out_path, checker, in_path, python, case_dir_name):
    if result["status"] != "ok":
        return False, result["status"]
    actual = result["actual"]
    if checker:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(actual, tf)
            actual_path = tf.name
        try:
            c = subprocess.run([python, checker, in_path, out_path or "", actual_path], capture_output=True, timeout=30)
            return c.returncode == 0, (c.stdout.decode(errors="replace").strip()[:300] or "checker")
        finally:
            os.unlink(actual_path)
    if out_path is None:
        return False, "malformed case: no expected stdout and no check.py"
    ok = norm_lines(actual["stdout"]) == norm_lines(open(out_path, encoding="utf-8").read())
    if not ok:
        return False, "stdout mismatch"
    exp_file = out_path[: -len(".stdout.txt")] + ".outfile.txt"
    if os.path.exists(exp_file):
        if norm_lines(actual["outfile"]) != norm_lines(open(exp_file, encoding="utf-8").read()):
            return False, "output file mismatch"
    return True, "match"


def run_case(solution, entry, python, in_path, timeout):
    with open(in_path, "rb") as fh:
        stdin = fh.read()
    t0 = time.time()
    try:
        p = subprocess.run(
            [python, entry], cwd=solution, input=stdin,
            capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "wall_s": round(time.time() - t0, 3)}
    except FileNotFoundError as e:
        return {"status": "no_entry", "error": str(e), "wall_s": 0}
    wall = round(time.time() - t0, 3)
    if p.returncode != 0:
        return {"status": "crash", "returncode": p.returncode,
                "stderr": p.stderr.decode(errors="replace")[-2000:], "wall_s": wall}
    try:
        actual = json.loads(p.stdout.decode())
    except Exception as e:
        return {"status": "bad_output", "error": str(e),
                "stdout": p.stdout.decode(errors="replace")[-500:], "wall_s": wall}
    return {"status": "ok", "actual": actual, "wall_s": wall}


def judge(result, out_path, checker, in_path, python):
    if result["status"] != "ok":
        return False, result["status"]
    actual = result["actual"]
    if checker:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(actual, tf)
            actual_path = tf.name
        try:
            c = subprocess.run([python, checker, in_path, out_path or "", actual_path],
                               capture_output=True, timeout=30)
            return c.returncode == 0, (c.stdout.decode(errors="replace").strip()[:300] or "checker")
        finally:
            os.unlink(actual_path)
    if out_path is None:
        return False, "malformed case: no expected output and no check.py"
    try:
        with open(out_path) as fh:
            expected = json.load(fh)
    except FileNotFoundError:
        return False, "malformed case: expected output file is missing"
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return False, f"malformed case: expected output is not JSON ({e})"
    return actual == expected, ("match" if actual == expected else "mismatch")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--entry", default="solve.py")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--python", default=sys.executable or "python3")
    ap.add_argument("--json", action="store_true", help="print only the JSON summary")
    a = ap.parse_args()

    if not os.path.exists(os.path.join(a.solution, a.entry)):
        summary = {"solution_started": False, "categories": {}, "error": f"missing {a.entry}"}
        for cat, cases in discover(a.tests).items():
            summary["categories"][cat] = {"pass": 0, "total": len(cases), "cases": []}
        print(json.dumps(summary, indent=None if a.json else 2))
        return 2

    summary = {"solution_started": True, "categories": {}}
    for cat, cases in discover(a.tests).items():
        rec = {"pass": 0, "total": len(cases), "cases": []}
        for name, in_path, out_path, checker, mode in cases:
            try:
                if mode == "argv":
                    args_path = in_path[: -len(".in.txt")] + ".args"
                    r = run_case_argv(a.solution, a.entry, a.python, in_path, args_path, a.timeout)
                    ok, why = judge_argv(r, out_path, checker, in_path, a.python, cat)
                else:
                    r = run_case(a.solution, a.entry, a.python, in_path, a.timeout)
                    ok, why = judge(r, out_path, checker, in_path, a.python)
            except Exception as e:
                # One broken case fails that case. It must never stop the other cases,
                # which would turn a fixture mistake into a zero for every student.
                r, ok, why = {"wall_s": None}, False, f"case error: {type(e).__name__}: {e}"
            rec["pass"] += int(ok)
            rec["cases"].append({"name": name, "pass": ok, "why": why, "wall_s": r.get("wall_s")})
            if not a.json:
                print(f"[{cat}] {name}: {'PASS' if ok else 'FAIL'} ({why}, {r.get('wall_s')}s)", file=sys.stderr)
        summary["categories"][cat] = rec
    print(json.dumps(summary, indent=None if a.json else 2))
    total = sum(c["total"] for c in summary["categories"].values())
    passed = sum(c["pass"] for c in summary["categories"].values())
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

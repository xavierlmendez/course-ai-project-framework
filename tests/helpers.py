"""Fixture builders for the tool tests. Standard library only.

Every test builds its own project and cohort in a temporary directory, so tests
are order-independent and leave nothing behind. Nothing here needs Docker,
Ollama, or the network.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")


def tool(name):
    return os.path.join(TOOLS, name)


def run_tool(name, *args, stdin=None, expect_ok=None):
    """Run a tool and return (returncode, stdout, stderr)."""
    p = subprocess.run([sys.executable, tool(name), *[str(a) for a in args]],
                       capture_output=True, text=True, input=stdin, timeout=300)
    if expect_ok is True and p.returncode != 0:
        raise AssertionError(f"{name} failed ({p.returncode}):\n{p.stderr}")
    return p.returncode, p.stdout, p.stderr


def parse_csv(text):
    import csv as _csv
    rows = list(_csv.DictReader(text.splitlines()))
    return {r["student_id"]: r for r in rows}


class TempCase(unittest.TestCase):
    """Test case with a scratch directory removed on teardown."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="frameworktest-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def path(self, *parts):
        p = os.path.join(self.dir, *parts)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def write(self, relpath, content):
        p = self.path(relpath)
        with open(p, "w") as fh:
            fh.write(content)
        return p

    def write_json(self, relpath, obj):
        return self.write(relpath, json.dumps(obj, indent=1))

    # ---------- project ----------

    DEFAULT_CATEGORIES = {
        "basic": {"weight": 1, "policy": "strict"},
        "twist_rule": {"weight": 2, "twist": True, "policy": "strict"},
        "grad_hard": {"weight": 1, "grad_only": True, "policy": "strict"},
    }

    def make_project(self, name="demo", ptype="B", categories=None, **extra):
        """Write project.json and return its path. Weights satisfy the twist rule:
        non-grad weights are basic 1 + twist 2 = 3, twist half would be 1.5, so tests
        that care about the rule pass their own categories."""
        cats = self.DEFAULT_CATEGORIES if categories is None else categories
        proj = {
            "name": name,
            "type": ptype,
            "entry": "solve.py",
            "python": sys.executable,
            "base_model": "test-model",
            "resource_host": "resource.invalid",
            "ollama_host": "http://ollama.invalid:11434",
            "k": 3,
            "temperatures": [0.2, 0.6, 1.0],
            "hidden_points": 70,
            "milestone_points": 10,
            "written_points": 20,
            "categories": cats,
        }
        proj.update(extra)
        return self.write_json("project.json", proj)

    def make_seeds(self, seeds=(11, 22, 33)):
        return self.write_json("seeds.secret.json", {"seeds": list(seeds)})

    # ---------- run records ----------

    def make_record(self, sid, filename, categories, complete=True, ptype="B", slot=1,
                    started=True, run_tag=None, **extra):
        """Write one runner record. `categories` maps name -> (pass, total)."""
        rec = {
            "submission": sid,
            "type": ptype,
            "complete": complete,
            "tests": {
                "solution_started": started,
                "categories": {k: {"pass": v[0], "total": v[1]} for k, v in categories.items()},
            },
        }
        if ptype == "B":
            rec["slot"] = slot
            rec["run_tag"] = run_tag or f"grading-k{slot}"
        rec.update(extra)
        return self.write_json(os.path.join("runs", sid, filename), rec)

    def perfect(self, sid, cats=None, slots=(1, 2, 3)):
        """A submission that passes everything in every slot."""
        cats = cats or self.DEFAULT_CATEGORIES
        scores = {c: (4, 4) for c in cats}
        for s in slots:
            self.make_record(sid, f"k{s}.json", scores, slot=s)

    # ---------- cohort csvs ----------

    def make_status(self, rows, header="student_id,status,grad,note"):
        """rows: list of tuples matching the header."""
        lines = [header] + [",".join(str(x) for x in r) for r in rows]
        return self.write("status.csv", "\n".join(lines) + "\n")

    def make_written(self, rows, header="student_id,accuracy,twist,candor,prediction"):
        lines = [header] + [",".join(str(x) for x in r) for r in rows]
        return self.write("written.csv", "\n".join(lines) + "\n")

    def make_milestone(self, rows, header="student_id,milestone"):
        lines = [header] + [",".join(str(x) for x in r) for r in rows]
        return self.write("milestone.csv", "\n".join(lines) + "\n")

    # ---------- test suites on disk ----------

    def make_test_suite(self, relpath, categories, mode="stdio"):
        """categories: {name: n_cases}. Cases are trivial identity checks."""
        for cat, n in categories.items():
            for i in range(1, n + 1):
                base = os.path.join(relpath, cat, f"{i:03d}")
                if mode == "stdio":
                    self.write_json(base + ".in.json", {"n": i})
                    self.write_json(base + ".out.json", {"n": i})
                else:
                    self.write(base + ".args", "{in} {out}\n")
                    self.write(base + ".in.txt", str(i))
                    self.write(base + ".stdout.txt", f"value: {i}\n")
        return self.path(relpath)

    def make_solution(self, relpath="solution", mode="stdio", correct=True):
        """A solve.py that echoes its input, or gets it wrong when correct=False."""
        if mode == "stdio":
            body = ("import json,sys\n"
                    "d=json.load(sys.stdin)\n"
                    f"print(json.dumps({{'n': d['n']{'' if correct else '+1'}}}))\n")
        else:
            body = ("import sys\n"
                    "v=open(sys.argv[1]).read().strip()\n"
                    f"print('value: '+str(int(v){'' if correct else '+1'}))\n"
                    "open(sys.argv[2],'w').write(v)\n")
        self.write(os.path.join(relpath, "solve.py"), body)
        return self.path(relpath)

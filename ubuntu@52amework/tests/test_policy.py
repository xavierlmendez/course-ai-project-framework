"""F-34: the equivalence policy is declared in project.json and enforced by the tools.

framework.md section 9 and templates/twist-checklist.md both require every hidden
category to name its equivalence policy. Before this slice nothing read it, so a
category could declare "estimate" and still be graded by exact comparison. These tests
pin the three rules: a non-strict policy needs a check.py, a strict one must not have
one, and the declared policy is reported beside the marks it produced.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool  # noqa: E402

CHECKER = ("import sys\n"
           "print('checker ran')\n"
           "sys.exit(0)\n")


def summary_of(out):
    return json.loads(out.strip().splitlines()[-1])


class TestPolicyEnforcement(TempCase):

    def make_suite_and_solution(self, categories):
        self.make_test_suite("tests", categories)
        return self.make_solution()

    def test_non_strict_policy_without_checker_is_refused(self):
        """A policy other than strict is realised only by a check.py. Declaring
        "estimate" with no checker would silently grade by exact comparison, which is
        exactly the wrong-grade path F-34 describes."""
        sol = self.make_suite_and_solution({"basic": 2})
        proj = self.make_project(categories={"basic": {"weight": 1, "policy": "estimate"}})
        code, out, err = run_tool("run_tests.py", "--solution", sol,
                                  "--tests", self.path("tests"), "--project", proj, "--json")
        self.assertEqual(code, 2)
        self.assertIn("basic", err)
        self.assertIn("estimate", err)
        self.assertIn("check.py", err)
        r = summary_of(out)
        self.assertFalse(r["solution_started"])
        self.assertIn("equivalence policy", r["error"])

    def test_strict_policy_with_a_checker_is_refused(self):
        """A checker decides equivalence whatever the declaration says, so a category
        that ships one while declaring strict is graded by a rule nobody wrote down."""
        sol = self.make_suite_and_solution({"basic": 2})
        self.write(os.path.join("tests", "basic", "check.py"), CHECKER)
        proj = self.make_project(categories={"basic": {"weight": 1, "policy": "strict"}})
        code, out, err = run_tool("run_tests.py", "--solution", sol,
                                  "--tests", self.path("tests"), "--project", proj, "--json")
        self.assertEqual(code, 2)
        self.assertIn("basic", err)
        self.assertIn("check.py", err)
        r = summary_of(out)
        self.assertIn("equivalence policy", r["error"])

    def test_unknown_policy_is_refused(self):
        sol = self.make_suite_and_solution({"basic": 1})
        proj = self.make_project(categories={"basic": {"weight": 1, "policy": "vibes"}})
        code, _, err = run_tool("run_tests.py", "--solution", sol,
                                "--tests", self.path("tests"), "--project", proj, "--json")
        self.assertEqual(code, 2)
        self.assertIn("vibes", err)

    def test_declared_policy_appears_in_the_summary(self):
        """The TA reading a run record can see which rule produced each mark."""
        sol = self.make_suite_and_solution({"basic": 2, "twist_rule": 1})
        self.write(os.path.join("tests", "twist_rule", "check.py"), CHECKER)
        proj = self.make_project(categories={
            "basic": {"weight": 1, "policy": "strict"},
            "twist_rule": {"weight": 1, "twist": True, "policy": "valid"},
        })
        code, out, _ = run_tool("run_tests.py", "--solution", sol,
                                "--tests", self.path("tests"), "--project", proj, "--json")
        self.assertEqual(code, 0)
        cats = summary_of(out)["categories"]
        self.assertEqual(cats["basic"]["policy"], "strict")
        self.assertEqual(cats["twist_rule"]["policy"], "valid")
        self.assertEqual(cats["basic"]["pass"], 2)

    def test_category_absent_from_project_reports_no_policy(self):
        """A test directory the project does not declare is not policed here; the
        undeclared-category FAIL belongs to review_checks.py."""
        sol = self.make_suite_and_solution({"basic": 1, "stray": 1})
        proj = self.make_project(categories={"basic": {"weight": 1, "policy": "strict"}})
        code, out, _ = run_tool("run_tests.py", "--solution", sol,
                                "--tests", self.path("tests"), "--project", proj, "--json")
        self.assertEqual(code, 0)
        self.assertIsNone(summary_of(out)["categories"]["stray"]["policy"])


class TestWithoutProjectBehaviourIsUnchanged(TempCase):
    """Students and the milestone run the public suite with no project.json to hand."""

    def test_no_project_flag_means_no_policy_and_no_refusal(self):
        self.make_test_suite("tests", {"basic": 2})
        self.write(os.path.join("tests", "basic", "check.py"), CHECKER)
        sol = self.make_solution()
        # The same layout that --project refuses (checker + strict) runs normally here.
        self.make_project(categories={"basic": {"weight": 1, "policy": "strict"}})
        code, out, _ = run_tool("run_tests.py", "--solution", sol,
                                "--tests", self.path("tests"), "--json")
        self.assertEqual(code, 0)
        rec = summary_of(out)["categories"]["basic"]
        self.assertNotIn("policy", rec)
        self.assertEqual(rec["pass"], 2)


class TestExamplesDeclarePolicies(unittest.TestCase):
    """Every category in every shipped example names its policy (fix-plan slice 5.1)."""

    def test_every_example_category_has_a_policy(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        found = 0
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, "examples")):
            if "project.json" not in filenames:
                continue
            path = os.path.join(dirpath, "project.json")
            with open(path) as fh:
                cats = (json.load(fh).get("categories") or {})
            for name, meta in cats.items():
                found += 1
                self.assertIn("policy", meta, f"{path}: category {name} declares no policy")
                self.assertIn(meta["policy"], ("strict", "estimate", "ab", "valid"),
                              f"{path}: category {name} has policy {meta['policy']!r}")
        self.assertGreater(found, 0)


if __name__ == "__main__":
    unittest.main()

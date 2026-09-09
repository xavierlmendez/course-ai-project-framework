"""grade.py: the arithmetic that decides a student's grade.

Every test names the finding from docs/review/findings.md that it guards.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, parse_csv  # noqa: E402


class TestGradArithmetic(TempCase):
    """F-02: a graduate must be graded on the graduate bar."""

    def test_grad_only_category_counts_for_a_graduate(self):
        self.make_project()
        # basic 1/1, twist 4/4, grad_hard 0/4
        self.make_record("ABC123456", "k1.json", {"basic": (1, 1), "twist_rule": (4, 4), "grad_hard": (0, 4)})
        self.make_status([("ABC123456", "graded", 1, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        # weights basic 1 + twist 2 + grad 1 = 4; fractions 1, 1, 0 -> (1*1 + 2*1 + 1*0)/4 = 0.75
        self.assertAlmostEqual(float(row["hidden_score"]), 0.75 * 70, places=2)
        self.assertEqual(row["grad"], "1")

    def test_grad_only_category_excluded_for_undergraduate(self):
        self.make_project()
        self.make_record("DEF654321", "k1.json", {"basic": (1, 1), "twist_rule": (4, 4), "grad_hard": (0, 4)})
        self.make_status([("DEF654321", "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)["DEF654321"]
        # grad_hard dropped: weights 1 + 2 = 3, both perfect -> full marks
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2)

    def test_missing_grad_column_is_refused(self):
        """F-02: silently defaulting every graduate to the undergraduate bar is the
        failure mode. A status.csv without the column must be an error, not a default."""
        self.make_project()
        self.make_record("ABC123456", "k1.json", {"basic": (1, 1), "twist_rule": (4, 4), "grad_hard": (0, 4)})
        self.make_status([("ABC123456", "graded", "")], header="student_id,status,note")
        code, out, err = run_tool("grade.py", "--project", self.path("project.json"),
                                  "--runs", self.path("runs"), "--status", self.path("status.csv"))
        self.assertNotEqual(code, 0, "grade.py accepted a status.csv with no grad column")
        self.assertIn("grad", (err or "").lower())


class TestComponentCompleteness(TempCase):
    """F-16: a total must not be emitted when a component is missing."""

    def test_total_absent_when_written_and_milestone_missing(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["total"], "", "a total was emitted with no written or milestone score")
        self.assertEqual(row["status"], "incomplete")

    def test_perfect_student_scores_exactly_100(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"), expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["total"]), 100.0, places=2)

    def test_empty_category_does_not_penalise(self):
        """F-16: a declared category with no test cases must not add weight to the
        denominator, which would cap every student below full marks."""
        cats = dict(TempCase.DEFAULT_CATEGORIES)
        cats["ghost"] = {"weight": 1, "policy": "strict"}
        self.make_project(categories=cats)
        self.make_record("ABC123456", "k1.json",
                         {"basic": (1, 1), "twist_rule": (4, 4), "ghost": (0, 0)})
        self.make_status([("ABC123456", "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2,
                               msg="an empty category silently reduced the score")


class TestWrittenScores(TempCase):
    """F-17: written dimensions must stay inside the rubric's range."""

    def test_dimension_above_three_is_refused(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        self.make_written([("ABC123456", 3, 9, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        code, out, err = run_tool("grade.py", "--project", self.path("project.json"),
                                  "--runs", self.path("runs"), "--status", self.path("status.csv"),
                                  "--written", self.path("written.csv"),
                                  "--milestone", self.path("milestone.csv"))
        self.assertNotEqual(code, 0, "a written dimension of 9 was accepted")

    def test_negative_dimension_is_refused(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        self.make_written([("ABC123456", -1, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        code, _, _ = run_tool("grade.py", "--project", self.path("project.json"),
                              "--runs", self.path("runs"), "--status", self.path("status.csv"),
                              "--written", self.path("written.csv"),
                              "--milestone", self.path("milestone.csv"))
        self.assertNotEqual(code, 0, "a negative written dimension was accepted")

    def test_graduate_written_uses_four_dimensions(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 1, "")])
        self.make_written([("ABC123456", 3, 3, 3, 0)])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"), expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        # 9 of a possible 12 -> 15 of 20
        self.assertAlmostEqual(float(row["written_score"]), 15.0, places=2)


class TestBestOfK(TempCase):
    """The best-of-K policy from framework.md section 6."""

    def test_best_slot_wins(self):
        self.make_project()
        sid = "ABC123456"
        self.make_record(sid, "k1.json", {"basic": (0, 1), "twist_rule": (0, 4)}, slot=1)
        self.make_record(sid, "k2.json", {"basic": (1, 1), "twist_rule": (4, 4)}, slot=2)
        self.make_record(sid, "k3.json", {"basic": (1, 1), "twist_rule": (2, 4)}, slot=3)
        self.make_status([(sid, "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)[sid]
        self.assertEqual(row["best_slot"], "2")
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2)

    def test_incomplete_records_are_ignored(self):
        self.make_project()
        sid = "ABC123456"
        self.make_record(sid, "k1.json", {"basic": (1, 1), "twist_rule": (4, 4)}, slot=1, complete=False)
        self.make_record(sid, "k2.json", {"basic": (0, 1), "twist_rule": (0, 4)}, slot=2)
        self.make_status([(sid, "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)[sid]
        self.assertEqual(row["best_slot"], "2")

    def test_appeal_record_is_considered(self):
        """F-05: an appeal writes its own record and must be able to raise the grade."""
        self.make_project()
        sid = "ABC123456"
        self.make_record(sid, "k2.json", {"basic": (0, 1), "twist_rule": (0, 4)}, slot=2)
        self.make_record(sid, "appeal-k2.json", {"basic": (1, 1), "twist_rule": (4, 4)},
                         slot=2, run_tag="appeal-k2")
        self.make_status([(sid, "appeal", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)[sid]
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2)


class TestIncompleteWording(TempCase):
    """A Type A project has no slots: the student submits code and it is run once. The note
    still said "1 slot(s) never completed", which sent a TA looking for the other slots."""

    def test_type_a_says_the_run_never_completed(self):
        self.make_project(ptype="A")
        sid = "ABC123456"
        self.make_record(sid, "run.json", {}, complete=False, ptype="A")
        self.make_status([(sid, "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        note = parse_csv(out)[sid]["note"]
        self.assertIn("the run never completed", note)
        self.assertNotIn("slot(s)", note)

    def test_type_b_still_counts_the_slots(self):
        self.make_project(ptype="B")
        sid = "ABC123456"
        self.make_record(sid, "k1.json", {}, complete=False, slot=1)
        self.make_record(sid, "k2.json", {}, complete=False, slot=2)
        self.make_status([(sid, "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        self.assertIn("2 slot(s) never completed", parse_csv(out)[sid]["note"])


if __name__ == "__main__":
    unittest.main()

"""combine_parts.py: how a multi-part project composes into one grade.

Decision 3 in docs/review/fix-plan.md: a part contributes only its hidden-test
score, weighted by part weight, to the 70. Milestone and written are course-level
and counted once. F-04.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, parse_csv  # noqa: E402

PART_HEADER = "student_id,status,grad,best_slot,hidden_score,milestone,written_raw,written_score,total,note"


class TestCombineParts(TempCase):

    def make_parts(self, weights):
        return self.write_json("parts.json",
                               {"parts": [{"name": n, "weight": w} for n, w in weights]})

    def make_part_book(self, filename, rows):
        """rows: (student_id, status, grad, hidden_score[, note])."""
        lines = [PART_HEADER]
        for row in rows:
            sid, status, grad, hidden = row[:4]
            note = row[4] if len(row) > 4 else ""
            lines.append(f"{sid},{status},{grad},1,{hidden},,,,,\"{note}\"")
        return self.write(filename, "\n".join(lines) + "\n")

    def test_perfect_student_scores_exactly_100(self):
        """The bug: weighting each part's whole total counted the written component
        once per part and produced 94.5 for a perfect student."""
        self.make_parts([("I", 45), ("II", 35), ("III", 10), ("IV", 10)])
        for i, n in enumerate(["I", "II", "III", "IV"], start=1):
            self.make_part_book(f"gb{i}.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"),
                             *[self.path(f"gb{i}.csv") for i in range(1, 5)], expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["total"]), 100.0, places=2)
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2)

    def test_hidden_is_weighted_by_part(self):
        self.make_parts([("I", 45), ("II", 35), ("III", 10), ("IV", 10)])
        # full marks on part I only
        for i, hidden in enumerate([70.0, 0.0, 0.0, 0.0], start=1):
            self.make_part_book(f"gb{i}.csv", [("ABC123456", "graded", 0, hidden)])
        self.make_written([("ABC123456", 0, 0, 0, "")])
        self.make_milestone([("ABC123456", 0)])
        _, out, _ = run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"),
                             *[self.path(f"gb{i}.csv") for i in range(1, 5)], expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0 * 0.45, places=2)
        self.assertAlmostEqual(float(row["total"]), 31.5, places=2)

    def test_written_counted_once_not_per_part(self):
        self.make_parts([("I", 50), ("II", 50)])
        for i in (1, 2):
            self.make_part_book(f"gb{i}.csv", [("ABC123456", "graded", 0, 0.0)])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 0)])
        _, out, _ = run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"),
                             self.path("gb1.csv"), self.path("gb2.csv"), expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["written_score"]), 20.0, places=2)
        self.assertAlmostEqual(float(row["total"]), 20.0, places=2)

    def test_incomplete_part_blocks_the_total(self):
        self.make_parts([("I", 50), ("II", 50)])
        self.make_part_book("gb1.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_part_book("gb2.csv", [("ABC123456", "incomplete", 0, "")])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"),
                             self.path("gb1.csv"), self.path("gb2.csv"), expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["total"], "")
        self.assertEqual(row["status"], "incomplete")

    def test_graduate_written_denominator(self):
        self.make_parts([("I", 100)])
        self.make_part_book("gb1.csv", [("ABC123456", "graded", 1, 70.0)])
        self.make_written([("ABC123456", 3, 3, 3, 0)])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                             "--written", self.path("written.csv"),
                             "--milestone", self.path("milestone.csv"),
                             self.path("gb1.csv"), expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertAlmostEqual(float(row["written_score"]), 15.0, places=2)


class TestPartNotesSurvive(TempCase):
    """Cold run 4: `grade.py --hidden-only` writes grade-relevant per-part notes such as
    `1 slot(s) never completed`, and combine_parts dropped them, so the runbook's readiness
    check reported every row ready to send."""

    make_parts = TestCombineParts.make_parts
    make_part_book = TestCombineParts.make_part_book

    def combine(self):
        return run_tool("combine_parts.py", "--parts", self.path("parts.json"),
                        "--written", self.path("written.csv"),
                        "--milestone", self.path("milestone.csv"),
                        self.path("gb1.csv"), self.path("gb2.csv"), expect_ok=True)

    def test_a_part_note_reaches_the_combined_note(self):
        self.make_parts([("I", 45), ("II", 35)])
        self.make_part_book("gb1.csv",
                            [("ABC123456", "graded", 0, 70.0, "1 slot(s) never completed")])
        self.make_part_book("gb2.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = self.combine()
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["status"], "graded")
        self.assertEqual(row["note"], "I: 1 slot(s) never completed",
                         "a part's note was dropped from the combined gradebook")

    def test_notes_from_several_parts_are_all_named(self):
        self.make_parts([("I", 45), ("II", 35)])
        self.make_part_book("gb1.csv", [("ABC123456", "graded", 0, 70.0, "2 slot(s) never completed")])
        self.make_part_book("gb2.csv", [("ABC123456", "graded", 0, 70.0, "1 slot(s) never completed")])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = self.combine()
        self.assertEqual(parse_csv(out)["ABC123456"]["note"],
                         "I: 2 slot(s) never completed; II: 1 slot(s) never completed")

    def test_the_missing_clause_still_appears_after_the_part_notes(self):
        self.make_parts([("I", 45), ("II", 35)])
        self.make_part_book("gb1.csv",
                            [("ABC123456", "graded", 0, 70.0, "1 slot(s) never completed")])
        self.make_part_book("gb2.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_written([("ZZZ999999", 3, 3, 3, "")])   # no written row for ABC123456
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = self.combine()
        self.assertEqual(parse_csv(out)["ABC123456"]["note"],
                         "I: 1 slot(s) never completed; missing: written")

    def test_a_clean_row_still_has_an_empty_note(self):
        self.make_parts([("I", 45), ("II", 35)])
        self.make_part_book("gb1.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_part_book("gb2.csv", [("ABC123456", "graded", 0, 70.0)])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        self.make_milestone([("ABC123456", 1)])
        _, out, _ = self.combine()
        self.assertEqual(parse_csv(out)["ABC123456"]["note"], "")


class TestPartMode(TempCase):
    """A part gradebook carries the hidden score only; the course-level components are
    added once by combine_parts."""

    def test_part_project_is_graded_without_written_or_milestone(self):
        self.make_project(part="I", spec="SPEC-part-I.md")
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["status"], "graded",
                         "a part was marked incomplete for lacking course-level components")
        self.assertAlmostEqual(float(row["hidden_score"]), 70.0, places=2)
        self.assertEqual(row["total"], "", "a part emitted a total of its own")

    def test_single_part_project_still_requires_every_component(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        _, out, _ = run_tool("grade.py", "--project", self.path("project.json"),
                             "--runs", self.path("runs"), "--status", self.path("status.csv"),
                             expect_ok=True)
        self.assertEqual(parse_csv(out)["ABC123456"]["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()

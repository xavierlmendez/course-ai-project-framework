"""milestone.py: the 10 points that prove a student got the reference setup working.

F-39 and decision 11.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, parse_csv  # noqa: E402


class MilestoneCase(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo")
        self.make_test_suite("tests/public", {"basic": 2})
        os.makedirs(self.path("records"), exist_ok=True)

    def practice_run(self, sid, correct=True, **overrides):
        """A completed practice run: the work directory the harness wrote, and its record.

        Type B is the default project type, so every milestone record needs one.
        """
        work = self.make_solution(f"runs/{sid}/practice-k1-work", correct=correct)
        rec = {"submission": sid, "type": "B", "slot": 1, "run_tag": "practice-k1",
               "complete": True,
               "regeneration": {"harness_exit": 0, "wall_s": 12.0, "entry_present": True}}
        rec.update(overrides)
        return work, self.write_json(f"runs/{sid}/practice-k1.json", rec)

    def record_for(self, sid, correct=True, out=None):
        work, reg = self.practice_run(sid, correct=correct)
        out = out or self.path(f"records/{sid}.json")
        return run_tool("milestone.py", "record", "--project", self.path("project.json"),
                        "--solution", work, "--student-id", sid,
                        "--regeneration", reg, "--out", out)


class TestRecord(MilestoneCase):

    def test_a_passing_run_writes_a_record(self):
        code, out, _ = self.record_for("ABC123456")
        self.assertEqual(code, 0, out)
        rec = json.load(open(self.path("records/ABC123456.json")))
        self.assertEqual(rec["student_id"], "ABC123456")
        self.assertEqual(rec["public"]["pass"], rec["public"]["total"])
        self.assertTrue(rec["digest"].startswith("sha256:"))

    def test_a_failing_run_is_reported_as_failing(self):
        code, out, _ = self.record_for("DEF654321", correct=False)
        self.assertNotEqual(code, 0, "a failing public suite produced a passing milestone")
        rec = json.load(open(self.path("records/DEF654321.json")))
        self.assertNotEqual(rec["public"]["pass"], rec["public"]["total"])


class TestCheck(MilestoneCase):

    def check(self, status=None):
        args = ["milestone.py", "check", "--project", self.path("project.json"),
                "--records", self.path("records")]
        if status:
            args += ["--status", status]
        return run_tool(*args)

    def test_passing_record_scores_the_milestone(self):
        self.record_for("ABC123456")
        _, out, _ = self.check()
        self.assertEqual(parse_csv(out)["ABC123456"]["milestone"], "1")

    def test_failing_record_scores_zero(self):
        self.record_for("DEF654321", correct=False)
        _, out, _ = self.check()
        row = parse_csv(out)["DEF654321"]
        self.assertEqual(row["milestone"], "0")
        self.assertIn("public suite", row["note"])

    def test_edited_record_is_rejected(self):
        """The digest exists so that turning a failing run into a passing one by opening
        the file is detectable."""
        self.record_for("DEF654321", correct=False)
        path = self.path("records/DEF654321.json")
        rec = json.load(open(path))
        rec["public"]["pass"] = rec["public"]["total"]
        json.dump(rec, open(path, "w"))
        _, out, _ = self.check()
        row = parse_csv(out)["DEF654321"]
        self.assertEqual(row["milestone"], "0", "an edited record was accepted")
        self.assertIn("digest", row["note"])

    def test_record_for_another_project_is_rejected(self):
        self.record_for("ABC123456")
        path = self.path("records/ABC123456.json")
        rec = json.load(open(path))
        rec["project"] = "some-other-course"
        # re-digest so only the project mismatch is under test
        import hashlib
        body = {k: v for k, v in rec.items() if k != "digest"}
        rec["digest"] = "sha256:" + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        json.dump(rec, open(path, "w"))
        _, out, _ = self.check()
        self.assertEqual(parse_csv(out)["ABC123456"]["milestone"], "0")

    def test_students_with_no_record_score_zero(self):
        self.record_for("ABC123456")
        status = self.make_status([("ABC123456", "graded", 0, ""), ("ZZZ999999", "graded", 0, "")])
        _, out, _ = self.check(status=status)
        rows = parse_csv(out)
        self.assertEqual(rows["ABC123456"]["milestone"], "1")
        self.assertEqual(rows["ZZZ999999"]["milestone"], "0")
        self.assertIn("no milestone record", rows["ZZZ999999"]["note"])

    def test_output_feeds_grade_py(self):
        """The whole point: the file this writes is the file grade.py reads."""
        self.record_for("ABC123456")
        _, out, _ = self.check()
        self.write("milestone.csv", out)
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        self.make_written([("ABC123456", 3, 3, 3, "")])
        _, gb, _ = run_tool("grade.py", "--project", self.path("project.json"),
                            "--runs", self.path("runs"), "--status", self.path("status.csv"),
                            "--written", self.path("written.csv"),
                            "--milestone", self.path("milestone.csv"), expect_ok=True)
        self.assertAlmostEqual(float(parse_csv(gb)["ABC123456"]["total"]), 100.0, places=2)


if __name__ == "__main__":
    unittest.main()

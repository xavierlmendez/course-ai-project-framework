"""runner.py: what gets executed, what gets recorded, and what gets resumed.

These tests never start Docker or a model. The harness call is replaced by a stub,
so what is under test is the runner's own bookkeeping.
"""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, ROOT  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))
import runner  # noqa: E402


def stub_regeneration(entry_present=True, **extra):
    """What regenerate() returns, without a harness."""
    rec = {"harness_exit": 0, "timed_out": False, "wall_s": 1.0,
           "harness_stdout_tail": "", "harness_stderr_tail": "",
           "entry_present": entry_present}
    rec.update(extra)
    return rec


class TestAppealRecords(TempCase):
    """F-05, F-14: a granted appeal must actually run and be distinguishable."""

    def setUp(self):
        super().setUp()
        self.make_project()
        self.make_seeds()
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.make_test_suite("tests/hidden", {"basic": 1})

    def test_appeal_writes_its_own_record(self):
        p = runner.load_project(self.path("project.json"))
        sub = self.path("submissions/ABC123456")
        out = self.path("runs")
        # a completed grading record already exists for slot 2
        self.make_record("ABC123456", "k2.json", {"basic": (0, 1)}, slot=2)
        with mock.patch.object(runner, "regenerate", return_value=stub_regeneration()), \
             mock.patch.object(runner, "run_tests", return_value={"solution_started": True,
                                                                  "categories": {"basic": {"pass": 1, "total": 1}}}):
            runner.process_type_b(p, "ABC123456", sub, out, [11, 22, 33], "appeal", [2], None, False, False)
        files = sorted(os.listdir(os.path.join(out, "ABC123456")))
        self.assertIn("appeal-k2.json", files,
                      f"the appeal produced no record of its own; found {files}")

    def test_grading_record_is_not_overwritten_by_an_appeal(self):
        p = runner.load_project(self.path("project.json"))
        sub = self.path("submissions/ABC123456")
        out = self.path("runs")
        self.make_record("ABC123456", "k2.json", {"basic": (0, 1)}, slot=2)
        with mock.patch.object(runner, "regenerate", return_value=stub_regeneration()), \
             mock.patch.object(runner, "run_tests", return_value={"solution_started": True,
                                                                  "categories": {"basic": {"pass": 1, "total": 1}}}):
            runner.process_type_b(p, "ABC123456", sub, out, [11, 22, 33], "appeal", [2], None, False, False)
        original = json.load(open(os.path.join(out, "ABC123456", "k2.json")))
        self.assertEqual(original["tests"]["categories"]["basic"]["pass"], 0,
                         "the appeal overwrote the original grading record")

    def test_a_grading_rerun_still_skips_completed_slots(self):
        """Resume must stay idempotent for ordinary grading."""
        p = runner.load_project(self.path("project.json"))
        sub = self.path("submissions/ABC123456")
        out = self.path("runs")
        self.make_record("ABC123456", "k2.json", {"basic": (0, 1)}, slot=2)
        called = []
        with mock.patch.object(runner, "regenerate", side_effect=lambda *a, **k: called.append(1) or stub_regeneration()), \
             mock.patch.object(runner, "run_tests", return_value={"solution_started": True, "categories": {}}):
            runner.process_type_b(p, "ABC123456", sub, out, [11, 22, 33], "grading", [2], None, False, False)
        self.assertEqual(called, [], "a completed grading slot was regenerated again")


class TestSubmissionIsolation(TempCase):
    """F-11: what reaches the container the student's specification runs in."""

    def setUp(self):
        super().setUp()
        self.make_project()
        self.make_seeds()
        self.make_test_suite("tests/hidden", {"basic": 1})

    def test_entry_file_in_a_submission_is_not_copied(self):
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.write("submissions/ABC123456/solve.py", "print('I brought my own answer')")
        p = runner.load_project(self.path("project.json"))
        workdir = self.path("work")
        runner.prepare_workdir(p, sub, workdir)
        self.assertFalse(os.path.exists(os.path.join(workdir, "solve.py")),
                         "the student's own solve.py was copied into the harness workdir")
        self.assertTrue(os.path.exists(os.path.join(workdir, "SPEC.md")))

    def test_solution_subdirectory_is_not_copied(self):
        """F-06: the calibration command pointed --submission at reference/, whose
        solution/ subdirectory holds the professor's own answer. Nothing but the
        specification and the data files it names may reach the harness workdir."""
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.write("submissions/ABC123456/solution/solve.py", "print('the professor answer')")
        p = runner.load_project(self.path("project.json"))
        workdir = self.path("work")
        runner.prepare_workdir(p, sub, workdir)
        self.assertFalse(os.path.exists(os.path.join(workdir, "solution")),
                         "a solution/ subdirectory was copied into the harness workdir")
        self.assertEqual(sorted(os.listdir(workdir)), ["SPEC.md"])

    def test_named_data_file_is_copied(self):
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC.md", "Use the table in board.txt when deciding.")
        self.write("submissions/ABC123456/board.txt", "xxxx")
        p = runner.load_project(self.path("project.json"))
        workdir = self.path("work")
        runner.prepare_workdir(p, sub, workdir)
        self.assertTrue(os.path.exists(os.path.join(workdir, "board.txt")),
                        "a data file the specification names was not provided to the harness")

    def test_project_directory_as_submission_is_refused(self):
        """Pointing --submission at a project copies the hidden tests, the reference
        solution and seeds.secret.json into the container, and recurses."""
        p = runner.load_project(self.path("project.json"))
        with self.assertRaises(runner.SubmissionError):
            runner.prepare_workdir(p, self.dir, self.path("work"))

    def test_submission_containing_the_output_directory_is_refused(self):
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC.md", "build it")
        os.makedirs(os.path.join(sub, "runs"), exist_ok=True)
        p = runner.load_project(self.path("project.json"))
        with self.assertRaises(runner.SubmissionError):
            runner.prepare_workdir(p, sub, os.path.join(sub, "runs", "work"))


class TestVariantSource(TempCase):
    """F-12: the roster decides a student's variant, not the student."""

    def setUp(self):
        super().setUp()
        self.write("gen.py", "import argparse,os,json\n"
                             "a=argparse.ArgumentParser();a.add_argument('--variant');a.add_argument('--out')\n"
                             "n=a.parse_args()\n"
                             "os.makedirs(os.path.join(n.out,'basic'),exist_ok=True)\n"
                             "open(os.path.join(n.out,'basic','used.txt'),'w').write(n.variant)\n")
        self.make_project(variants={"generator": "gen.py", "roster": "variants.csv"})
        self.write("variants.csv", "student_id,variant\nABC123456,alpha\n")
        self.write("submissions/ABC123456/SPEC.md", "build it")

    def test_variant_comes_from_the_roster(self):
        p = runner.load_project(self.path("project.json"))
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/variant.txt", "easy-mode")
        tests_dir, why = runner.resolve_tests(p, sub, None, False, sid="ABC123456")
        self.assertIsNone(why, why)
        used = open(os.path.join(tests_dir, "basic", "used.txt")).read().strip()
        self.assertEqual(used, "alpha",
                         "the student's variant.txt overrode the roster")

    def test_student_not_on_the_roster_is_an_error(self):
        p = runner.load_project(self.path("project.json"))
        sub = self.path("submissions/ABC123456")
        tests_dir, why = runner.resolve_tests(p, sub, None, False, sid="ZZZ999999")
        self.assertIsNotNone(why, "a student missing from the roster was silently graded")


class TestEnvironmentFailures(TempCase):
    """F-13 and decision 10: an environment failure must not score zero, and three
    in a row must stop the batch."""

    def setUp(self):
        super().setUp()
        self.make_project()
        self.make_seeds()
        self.make_test_suite("tests/hidden", {"basic": 1})
        for sid in ("AAA111111", "BBB222222", "CCC333333", "DDD444444"):
            self.write(f"submissions/{sid}/SPEC.md", "build it")

    def test_environment_failure_is_not_recorded_as_complete(self):
        p = runner.load_project(self.path("project.json"))
        out = self.path("runs")
        broken = stub_regeneration(entry_present=False, environment_error="docker daemon unreachable")
        with mock.patch.object(runner, "regenerate", return_value=broken):
            runner.process_type_b(p, "AAA111111", self.path("submissions/AAA111111"), out,
                                  [11, 22, 33], "grading", [1], None, False, False)
        rec = json.load(open(os.path.join(out, "AAA111111", "k1.json")))
        self.assertFalse(rec.get("complete"),
                         "an environment failure was recorded as a completed run scoring zero")

    def test_three_consecutive_failures_abort_the_batch(self):
        p = runner.load_project(self.path("project.json"))
        out = self.path("runs")
        broken = stub_regeneration(entry_present=False, environment_error="docker daemon unreachable")
        with mock.patch.object(runner, "regenerate", return_value=broken):
            with self.assertRaises(runner.BatchAborted):
                runner.run_batch(p, [(s, self.path(f"submissions/{s}"))
                                     for s in ("AAA111111", "BBB222222", "CCC333333", "DDD444444")],
                                 out, [11, 22, 33], "grading", [1], None, False, False, "B")

    def test_an_isolated_failure_does_not_abort(self):
        p = runner.load_project(self.path("project.json"))
        out = self.path("runs")
        seq = [stub_regeneration(entry_present=False, environment_error="blip"),
               stub_regeneration(), stub_regeneration(), stub_regeneration()]
        with mock.patch.object(runner, "regenerate", side_effect=seq), \
             mock.patch.object(runner, "run_tests", return_value={"solution_started": True,
                                                                  "categories": {"basic": {"pass": 1, "total": 1}}}):
            runner.run_batch(p, [(s, self.path(f"submissions/{s}"))
                                 for s in ("AAA111111", "BBB222222", "CCC333333", "DDD444444")],
                             out, [11, 22, 33], "grading", [1], None, False, False, "B")
        self.assertTrue(os.path.exists(os.path.join(out, "DDD444444", "k1.json")),
                        "one isolated failure stopped the batch")

    def test_a_failed_specification_still_scores_zero(self):
        """A harness that ran and produced nothing is the student's problem, not the
        environment's, and must be scored."""
        p = runner.load_project(self.path("project.json"))
        out = self.path("runs")
        with mock.patch.object(runner, "regenerate", return_value=stub_regeneration(entry_present=False)):
            runner.process_type_b(p, "AAA111111", self.path("submissions/AAA111111"), out,
                                  [11, 22, 33], "grading", [1], None, False, False)
        rec = json.load(open(os.path.join(out, "AAA111111", "k1.json")))
        self.assertTrue(rec.get("complete"), "a specification that produced nothing was not scored")
        self.assertEqual(rec["tests"]["categories"], {})


class TestSlotArguments(TempCase):
    """F-57: --slot must mean what it says."""

    def setUp(self):
        super().setUp()
        self.make_project()
        self.make_seeds()
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.make_test_suite("tests/hidden", {"basic": 1})

    def test_slot_zero_is_refused(self):
        code, _, err = run_tool("runner.py", "--project", self.path("project.json"),
                                "--submission", self.path("submissions/ABC123456"),
                                "--slot", "0", "--out", self.path("runs"), "--dry-run", "--no-sandbox")
        self.assertNotEqual(code, 0, "--slot 0 was accepted and silently ran every slot")

    def test_slot_above_k_is_refused(self):
        code, _, err = run_tool("runner.py", "--project", self.path("project.json"),
                                "--submission", self.path("submissions/ABC123456"),
                                "--slot", "4", "--out", self.path("runs"), "--dry-run", "--no-sandbox")
        self.assertNotEqual(code, 0, "--slot 4 was accepted for a K=3 project")


class TestMultiPartSpecs(TempCase):
    """Decision 19: one submission directory, one specification file per part."""

    def test_runner_reads_the_part_specification(self):
        self.make_project(part="I", spec="SPEC-part-I.md")
        self.make_seeds()
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC-part-I.md", "part one")
        self.write("submissions/ABC123456/SPEC-part-II.md", "part two")
        p = runner.load_project(self.path("project.json"))
        workdir = self.path("work")
        runner.prepare_workdir(p, sub, workdir)
        self.assertTrue(os.path.exists(os.path.join(workdir, "SPEC-part-I.md")))
        self.assertFalse(os.path.exists(os.path.join(workdir, "SPEC-part-II.md")),
                         "another part's specification was visible to this part's harness run")

    def test_wrapper_prompt_names_the_part_specification(self):
        self.make_project(part="I", spec="SPEC-part-I.md")
        p = runner.load_project(self.path("project.json"))
        prompt = runner.wrapper_prompt(p)
        self.assertIn("SPEC-part-I.md", prompt)


if __name__ == "__main__":
    unittest.main()

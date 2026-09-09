"""run_tests.py: the interface contract, both shapes of it."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool  # noqa: E402


class TestStdioContract(TempCase):

    def test_correct_solution_passes(self):
        self.make_test_suite("tests", {"basic": 2, "twist_rule": 2})
        sol = self.make_solution()
        code, out, _ = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        self.assertEqual(code, 0)
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 2)

    def test_wrong_solution_fails_every_case(self):
        self.make_test_suite("tests", {"basic": 2})
        sol = self.make_solution(correct=False)
        code, out, _ = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        self.assertNotEqual(code, 0)
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 0)

    def test_missing_entry_point_reports_not_started(self):
        self.make_test_suite("tests", {"basic": 1})
        os.makedirs(self.path("empty"), exist_ok=True)
        _, out, _ = run_tool("run_tests.py", "--solution", self.path("empty"),
                             "--tests", self.path("tests"), "--json")
        r = json.loads(out.strip().splitlines()[-1])
        self.assertFalse(r["solution_started"])


class TestMalformedCases(TempCase):
    """F-18: one bad case must fail one case, not the whole run."""

    def test_case_without_expected_output_fails_only_itself(self):
        self.make_test_suite("tests", {"basic": 2})
        # a third case with an input and no expected output and no checker
        self.write_json("tests/basic/003.in.json", {"n": 3})
        sol = self.make_solution()
        code, out, err = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        self.assertTrue(out.strip(), f"run_tests produced no JSON summary; stderr:\n{err}")
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["total"], 3)
        self.assertEqual(r["categories"]["basic"]["pass"], 2,
                         "a malformed case took the two good cases down with it")

    def test_unparsable_expected_output_fails_only_itself(self):
        self.make_test_suite("tests", {"basic": 2})
        self.write_json("tests/basic/003.in.json", {"n": 3})
        self.write("tests/basic/003.out.json", "{not json")
        sol = self.make_solution()
        _, out, err = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        self.assertTrue(out.strip(), f"run_tests produced no JSON summary; stderr:\n{err}")
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 2)


class TestArgvContract(TempCase):
    """The file-argument shape the professor's real project used."""

    def test_correct_solution_passes(self):
        self.make_test_suite("tests", {"basic": 2}, mode="argv")
        sol = self.make_solution(mode="argv")
        code, out, _ = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        self.assertEqual(code, 0)
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 2)

    def test_wrong_solution_fails(self):
        self.make_test_suite("tests", {"basic": 2}, mode="argv")
        sol = self.make_solution(mode="argv", correct=False)
        _, out, _ = run_tool("run_tests.py", "--solution", sol, "--tests", self.path("tests"), "--json")
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 0)


class TestTimeout(TempCase):

    def test_a_hanging_solution_times_out_and_does_not_hang_the_run(self):
        self.make_test_suite("tests", {"basic": 1})
        self.write("slow/solve.py", "import time\ntime.sleep(30)\n")
        _, out, _ = run_tool("run_tests.py", "--solution", self.path("slow"),
                             "--tests", self.path("tests"), "--timeout", "1", "--json")
        r = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(r["categories"]["basic"]["pass"], 0)
        self.assertEqual(r["categories"]["basic"]["cases"][0]["why"], "timeout")


if __name__ == "__main__":
    unittest.main()


class TestCaseDirIsHandedToTheSolutionUser(unittest.TestCase):
    """Inside the sandbox the runner is root and the solution is `runner`; the per-case
    temp directory must belong to the solution's user or every argv case crashes."""

    def test_chown_when_root_and_run_as(self):
        import pwd, tempfile, os
        from unittest import mock
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        import run_tests as rt
        tmp = tempfile.mkdtemp(); inp = os.path.join(tmp, "input.txt"); open(inp, "w").write("x")
        calls = []
        fake = pwd.struct_passwd(("runner", "x", 1001, 1001, "", "/home/runner", "/bin/bash"))
        with mock.patch.object(rt.os, "geteuid", lambda: 0), \
             mock.patch.object(rt.pwd, "getpwnam", lambda u: fake), \
             mock.patch.object(rt.os, "chown", lambda p, u, g: calls.append((p, u, g))):
            rt.hand_case_dir_to(tmp, inp, "runner")
        self.assertEqual(sorted(calls), sorted([(tmp, 1001, 1001), (inp, 1001, 1001)]))

    def test_no_chown_without_run_as(self):
        import tempfile, os
        from unittest import mock
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        import run_tests as rt
        tmp = tempfile.mkdtemp(); inp = os.path.join(tmp, "input.txt"); open(inp, "w").write("x")
        with mock.patch.object(rt.os, "chown", lambda *a: (_ for _ in ()).throw(AssertionError("chown called"))):
            rt.hand_case_dir_to(tmp, inp, None)

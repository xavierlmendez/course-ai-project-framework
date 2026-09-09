"""Defects found by the cold TA run of the runbook (Phase 3 exit criterion).

Each test names the friction-log entry it guards. The log is quoted in the Phase 3
section of docs/review/fix-plan.md.
"""
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, parse_csv, ROOT  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))
import runner  # noqa: E402


class TestSlotCheckReachesTheModel(TempCase):
    """#17: the slot check dialled host.docker.internal from the host, a name that only
    resolves inside the container, so it could never pass and it gated the whole batch."""

    def test_container_hostname_is_translated_for_host_side_checks(self):
        self.make_project(ollama_host="http://host.docker.internal:11434")
        p = runner.load_project(self.path("project.json"))
        url = runner.host_side_ollama(p)
        self.assertNotIn("host.docker.internal", url,
                         "the host-side check still uses a container-only hostname")
        self.assertIn("11434", url)

    def test_an_explicit_host_url_is_respected(self):
        self.make_project(ollama_host="http://host.docker.internal:11434",
                          ollama_host_local="http://10.0.0.5:11434")
        p = runner.load_project(self.path("project.json"))
        self.assertEqual(runner.host_side_ollama(p), "http://10.0.0.5:11434")

    def test_an_ordinary_hostname_is_left_alone(self):
        self.make_project(ollama_host="http://models.example.edu:11434")
        p = runner.load_project(self.path("project.json"))
        self.assertEqual(runner.host_side_ollama(p), "http://models.example.edu:11434")

    def test_an_unreachable_model_server_does_not_block_a_type_a_batch(self):
        """#15: Type A has no regeneration, so it needs neither seeds nor slots."""
        self.make_project(ptype="A")
        self.make_test_suite("tests/hidden", {"basic": 1})
        sol = self.make_solution("submissions/ABC123456")
        self.write("submissions/ABC123456/PROCESS.md", "x")
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--submissions", self.path("submissions"),
                                  "--type", "A", "--no-sandbox", "--out", self.path("runs"))
        self.assertEqual(code, 0, f"a Type A batch demanded seeds or a slot check:\n{err}")


class TestGradeMissingRuns(TempCase):
    """#25: a part with no runs directory crashed with a traceback and left a
    header-only CSV that combine_parts then turned into 'missing: a part'."""

    def test_missing_runs_directory_is_a_clean_error(self):
        self.make_project()
        self.make_status([("ABC123456", "graded", 0, "")])
        code, out, err = run_tool("grade.py", "--project", self.path("project.json"),
                                  "--runs", self.path("does-not-exist"),
                                  "--status", self.path("status.csv"))
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err, "a missing runs directory produced a traceback")
        self.assertIn("runs", err.lower())


class TestCsvLineEndings(TempCase):
    """#27: csv.writer's \\r\\n made the runbook's own sanity check flag every row."""

    def test_gradebook_lines_end_with_a_newline_only(self):
        self.make_project()
        self.perfect("ABC123456")
        self.make_status([("ABC123456", "graded", 0, "")])
        # subprocess text mode translates newlines, so the bytes have to be inspected the
        # way a shell redirect would leave them on disk.
        with open(self.path("gradebook.csv"), "wb") as fh:
            subprocess.run([sys.executable, os.path.join(ROOT, "tools", "grade.py"),
                            "--project", self.path("project.json"), "--runs", self.path("runs"),
                            "--status", self.path("status.csv")], stdout=fh, check=True)
        raw = open(self.path("gradebook.csv"), "rb").read()
        self.assertNotIn(b"\r", raw, "the gradebook on disk contains carriage returns, so the "
                                      "runbook's own sanity check flags every row")


class TestVariantRosterAcceptsPairs(TempCase):
    """#13: the roster split pair keys on '+' and ',' but the runbook mandates '-',
    so every pair was skipped with an exit code of 0."""

    def setUp(self):
        super().setUp()
        self.write("gen.py", "import argparse,os\n"
                             "a=argparse.ArgumentParser();a.add_argument('--variant');a.add_argument('--out')\n"
                             "n=a.parse_args()\n"
                             "os.makedirs(os.path.join(n.out,'basic'),exist_ok=True)\n"
                             "open(os.path.join(n.out,'basic','used.txt'),'w').write(n.variant)\n")
        self.make_project(variants={"generator": "gen.py", "roster": "variants.csv"})
        self.write("submissions/AAA111111-BBB222222/SPEC.md", "build it")

    def test_hyphenated_pair_directory_matches_a_plus_joined_roster(self):
        self.write("variants.csv", "student_id,variant\nAAA111111+BBB222222,alpha\n")
        p = runner.load_project(self.path("project.json"))
        _, why = runner.resolve_tests(p, self.path("submissions/AAA111111-BBB222222"),
                                      None, False, sid="AAA111111-BBB222222")
        self.assertIsNone(why, f"a pair was dropped: {why}")

    def test_a_skipped_submission_is_reported_at_the_end(self):
        """A SKIP line in the middle of a 65-line log is invisible."""
        self.write("variants.csv", "student_id,variant\nZZZ999999,alpha\n")
        self.make_test_suite("tests/hidden", {"basic": 1})
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--submissions", self.path("submissions"),
                                  "--type", "A", "--no-sandbox", "--out", self.path("runs"))
        self.assertIn("skipped", (out + err).lower())
        self.assertNotEqual(code, 0, "a batch that graded nobody exited 0")


class TestTypeAAppeal(TempCase):
    """#28: an appeal on a Type A project printed 'done, skipping' and did nothing."""

    def setUp(self):
        super().setUp()
        self.make_project(ptype="A")
        self.make_test_suite("tests/hidden", {"basic": 1})
        self.make_solution("submissions/ABC123456")

    def test_appeal_writes_its_own_record(self):
        out = self.path("runs")
        p = runner.load_project(self.path("project.json"))
        runner.process_type_a(p, "ABC123456", self.path("submissions/ABC123456"), out,
                              None, False, False)
        self.assertTrue(os.path.exists(os.path.join(out, "ABC123456", "a.json")))
        runner.process_type_a(p, "ABC123456", self.path("submissions/ABC123456"), out,
                              None, False, False, run_tag="appeal")
        files = sorted(os.listdir(os.path.join(out, "ABC123456")))
        self.assertIn("appeal-a.json", files,
                      f"a Type A appeal produced no record: {files}")


class TestMilestoneForTypeB(TempCase):
    """#20: a Type B student submits a specification and has no solution directory."""

    def test_record_can_be_made_from_a_practice_run_workdir(self):
        self.make_project(name="demo")
        self.make_test_suite("tests/public", {"basic": 1})
        work = self.make_solution("runs/ABC123456/practice-k1-work")
        # Type B also requires the runner record that produced that work directory.
        self.write_json("runs/ABC123456/practice-k1.json",
                        {"submission": "ABC123456", "type": "B", "slot": 1,
                         "run_tag": "practice-k1", "complete": True,
                         "regeneration": {"harness_exit": 0, "wall_s": 12.0,
                                          "entry_present": True}})
        code, out, _ = run_tool("milestone.py", "record",
                                "--project", self.path("project.json"),
                                "--solution", work, "--student-id", "ABC123456",
                                "--regeneration", self.path("runs/ABC123456/practice-k1.json"),
                                "--out", self.path("m.json"))
        self.assertEqual(code, 0, out)
        rec = json.load(open(self.path("m.json")))
        self.assertEqual(rec["public"]["pass"], rec["public"]["total"])


if __name__ == "__main__":
    unittest.main()


class TestOpenCodeTimeouts(TempCase):
    """OpenCode 1.18.29 aborts a provider request after 300 s of silence (measured on the
    R620, 2026-09-09: "ProviderHeaderTimeoutError: Provider response headers timed out after
    300000ms"). The generated config must lift both timeouts to the runner's own budget."""

    def test_header_and_chunk_timeouts_follow_the_regeneration_budget(self):
        p = {"ollama_host": "http://host.docker.internal:11434", "regeneration_timeout_s": 1800}
        runner.write_opencode_config(p, self.dir, "ref-x-slot1", temperature=0.2, seed=7)
        cfg = json.load(open(os.path.join(self.dir, "opencode.json")))
        opts = cfg["provider"]["ollama"]["options"]
        self.assertEqual(opts["headerTimeout"], 1800 * 1000)
        self.assertEqual(opts["chunkTimeout"], 1800 * 1000)
        self.assertEqual(opts["baseURL"], "http://host.docker.internal:11434/v1")


class TestHarnessLaunchDirectory(TempCase):
    """OpenCode 1.18.29 takes its project directory from the PWD variable, not the real cwd
    (R620, 2026-09-09: launched from the repo it opened a second instance there and died in
    4 s). The no-sandbox launch must therefore name the work directory both ways."""

    def test_no_sandbox_launch_sets_dir_and_pwd(self):
        p = {"slot_prefix": "ref-x-slot", "temperatures": [0.2], "ollama_host": "http://127.0.0.1:11434",
             "regeneration_timeout_s": 60, "entry": "solve.py", "spec": "SPEC.md", "name": "x",
             "data_files": [], "code_ext": [".py"]}
        sub = self.path("submissions", "ABC123456", "SPEC.md"); open(sub, "w").write("build it")
        work = self.path("runs", "ABC123456", "t-k1-work"); os.makedirs(work, exist_ok=True)
        seen = {}

        def fake_sh(cmd, timeout=None, cwd=None, dry=False, env=None):
            seen.update(cmd=cmd, cwd=cwd, env=env)
            return 1, "", "", 0.1

        with mock.patch.object(runner, "sh", fake_sh), \
             mock.patch.object(runner, "prepare_workdir", lambda *a, **k: None), \
             mock.patch.object(runner, "wrapper_prompt", lambda p: "go"):
            try:
                runner.regenerate(p, os.path.dirname(sub), work, 1, 7, "t", sandbox=False, dry=False)
            except Exception:
                pass  # the record-building after the launch is not under test here
        self.assertEqual(seen["cwd"], work)
        self.assertIn("--dir", seen["cmd"])
        self.assertEqual(seen["cmd"][seen["cmd"].index("--dir") + 1], work)
        self.assertEqual(seen["env"]["PWD"], work)

"""Phase 4b: defects a cold walk of the handouts found in the tools themselves.

1. milestone.py accepted a Type B record with no harness evidence at all.
2. create_slots() shelled out to a bare `ollama`, ignoring the project's model server.
3. A non-sandbox run pointed OpenCode at the container-only host name.
4. A missing `opencode` (or `docker`) binary gave a raw traceback.
5. --dry-run wrote records that looked exactly like real ones.
6. Slot Modelfiles carried no num_ctx, so slots ran at Ollama's 4096 default.

Nothing here starts Docker, Ollama, OpenCode or the network: every external call is
either mocked or expected to fail before it is made.
"""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, parse_csv, ROOT  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))
import runner  # noqa: E402


# ---------------------------------------------------------------- 1. milestone evidence

class MilestoneEvidenceCase(TempCase):
    """The milestone is the proof that the *harness* produced working code."""

    def setUp(self):
        super().setUp()
        self.make_project(name="demo")            # type B by default
        self.make_test_suite("tests/public", {"basic": 2})

    def practice_run(self, sid="ABC123456", correct=True, name="practice-k1.json",
                     workdir="practice-k1-work", **overrides):
        work = self.make_solution(f"runs/{sid}/{workdir}", correct=correct)
        rec = {"submission": sid, "type": "B", "slot": 1, "run_tag": "practice-k1",
               "complete": True,
               "regeneration": {"harness_exit": 0, "wall_s": 12.0, "entry_present": True}}
        rec.update(overrides)
        return work, self.write_json(f"runs/{sid}/{name}", rec)

    def record(self, *args, sid="ABC123456"):
        return run_tool("milestone.py", "record", "--project", self.path("project.json"),
                        "--student-id", sid, "--out", self.path("m.json"), *args)


class TestTypeBNeedsHarnessEvidence(MilestoneEvidenceCase):

    def test_a_missing_regeneration_flag_is_refused(self):
        work, _ = self.practice_run()
        code, out, err = self.record("--solution", work)
        self.assertNotEqual(code, 0, "a Type B milestone was written with no harness run")
        self.assertIn("--regeneration", err + out)
        self.assertFalse(os.path.exists(self.path("m.json")))

    def test_a_mistyped_regeneration_path_is_refused(self):
        work, _ = self.practice_run()
        code, out, err = self.record("--solution", work,
                                     "--regeneration", self.path("runs/ABC123456/practce-k1.json"))
        self.assertNotEqual(code, 0, "a typo'd regeneration path was silently ignored")
        self.assertIn("regeneration record not found", err + out)

    def test_a_file_that_is_not_a_runner_record_is_refused(self):
        work, _ = self.practice_run()
        other = self.write_json("runs/ABC123456/notes.json", {"hello": "world"})
        code, out, err = self.record("--solution", work, "--regeneration", other)
        self.assertNotEqual(code, 0)
        self.assertIn("not a runner record", err + out)

    def test_a_dry_run_record_is_refused(self):
        work, reg = self.practice_run(name="practice-k1.dry.json", complete=False, dry_run=True)
        code, out, err = self.record("--solution", work, "--regeneration", reg)
        self.assertNotEqual(code, 0, "a --dry-run record passed as evidence of a run")
        self.assertIn("dry-run record", err + out)

    def test_an_incomplete_run_is_refused(self):
        work, reg = self.practice_run(complete=False,
                                      incomplete_reason="environment: connection refused")
        code, out, err = self.record("--solution", work, "--regeneration", reg)
        self.assertNotEqual(code, 0)
        self.assertIn("not a completed run", err + out)

    def test_solution_must_be_that_records_work_directory(self):
        """Hand-written code beside a real run is exactly the hole this closes."""
        _, reg = self.practice_run()
        mine = self.make_solution("my-own-code")
        code, out, err = self.record("--solution", mine, "--regeneration", reg)
        self.assertNotEqual(code, 0, "hand-written code was accepted as a harness result")
        self.assertIn("not the directory that run wrote", err + out)

    def test_a_missing_solution_directory_says_so(self):
        _, reg = self.practice_run()
        code, out, err = self.record("--solution", self.path("nowhere"), "--regeneration", reg)
        self.assertNotEqual(code, 0)
        self.assertIn("--solution directory not found", err + out)

    def test_a_real_run_embeds_the_harness_block(self):
        work, reg = self.practice_run()
        code, out, err = self.record("--solution", work, "--regeneration", reg)
        self.assertEqual(code, 0, out + err)
        h = json.load(open(self.path("m.json")))["harness"]
        self.assertEqual(h["run_tag"], "practice-k1")
        self.assertEqual(h["slot"], 1)
        self.assertEqual(h["wall_s"], 12.0)
        self.assertEqual(h["model"], "test-model")
        self.assertTrue(h["entry_present"])
        self.assertTrue(h["complete"])
        self.assertEqual(h["record"], "practice-k1.json")

    def test_type_a_needs_no_regeneration(self):
        self.make_project(name="demo", ptype="A")
        sol = self.make_solution("submission")
        code, out, err = self.record("--solution", sol)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(json.load(open(self.path("m.json")))["type"], "A")


class TestCheckDemandsHarnessEvidence(MilestoneEvidenceCase):

    def write_record(self, sid="ABC123456", **mutate):
        work, reg = self.practice_run(sid=sid)
        os.makedirs(self.path("records"), exist_ok=True)
        code, out, err = run_tool("milestone.py", "record",
                                  "--project", self.path("project.json"),
                                  "--solution", work, "--regeneration", reg,
                                  "--student-id", sid, "--out", self.path(f"records/{sid}.json"),
                                  expect_ok=True)
        path = self.path(f"records/{sid}.json")
        if mutate:
            rec = json.load(open(path))
            for k, v in mutate.items():
                if v is None:
                    rec.pop(k, None)
                else:
                    rec[k] = v
            import hashlib
            body = {k: v for k, v in rec.items() if k != "digest"}
            rec["digest"] = "sha256:" + hashlib.sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            json.dump(rec, open(path, "w"))
        return path

    def check(self):
        return run_tool("milestone.py", "check", "--project", self.path("project.json"),
                        "--records", self.path("records"))

    def test_a_record_from_a_real_run_passes(self):
        self.write_record()
        _, out, _ = self.check()
        self.assertEqual(parse_csv(out)["ABC123456"]["milestone"], "1")

    def test_a_record_with_no_harness_block_is_refused(self):
        self.write_record(harness=None)
        _, out, _ = self.check()
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["milestone"], "0", "a milestone with no harness evidence scored")
        self.assertIn("no harness evidence", row["note"])

    def test_a_record_whose_run_never_produced_an_entry_point_is_refused(self):
        self.write_record(harness={"model": "test-model", "run_tag": "practice-k1", "slot": 1,
                                   "wall_s": 1.0, "entry_present": False, "complete": True,
                                   "record": "practice-k1.json"})
        _, out, _ = self.check()
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["milestone"], "0")
        self.assertIn("no harness evidence", row["note"])

    def test_a_record_whose_run_never_completed_is_refused(self):
        self.write_record(harness={"model": "test-model", "run_tag": "practice-k1", "slot": 1,
                                   "wall_s": 1.0, "entry_present": True, "complete": False,
                                   "record": "practice-k1.json"})
        _, out, _ = self.check()
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["milestone"], "0")
        self.assertIn("no harness evidence", row["note"])


# ------------------------------------------------- 2 & 6. model server host, num_ctx

class SlotCase(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo", ollama_host="http://host.docker.internal:11434")
        self.make_seeds()
        self.p = runner.load_project(self.path("project.json"))

    def create(self, dry=False):
        """create_slots with the ollama CLI replaced; returns the calls it made."""
        calls = []

        def fake_sh(cmd, timeout=None, cwd=None, dry=False, env=None):
            modelfile = open(cmd[-1]).read() if cmd[:2] == ["ollama", "create"] else ""
            calls.append({"cmd": cmd, "env": env, "modelfile": modelfile})
            return 0, "", "", 0.0

        with mock.patch.object(runner, "sh", fake_sh), \
             mock.patch.object(runner, "model_server_reachable", return_value=True):
            runner.create_slots(self.p, dry)
        return calls


class TestSlotCreationTargetsTheProjectsServer(SlotCase):

    def test_ollama_create_carries_the_projects_host(self):
        calls = self.create()
        self.assertEqual(len(calls), 3, calls)
        for c in calls:
            self.assertEqual(c["cmd"][:2], ["ollama", "create"])
            self.assertEqual(c["env"]["OLLAMA_HOST"], "http://127.0.0.1:11434",
                             "ollama create targeted whatever the CLI defaults to")

    def test_ollama_host_local_wins_for_the_cli(self):
        self.p["ollama_host_local"] = "http://course-server.example:11434"
        for c in self.create():
            self.assertEqual(c["env"]["OLLAMA_HOST"], "http://course-server.example:11434")

    def test_the_modelfile_pins_num_ctx(self):
        for c in self.create():
            self.assertIn("PARAMETER num_ctx 32768", c["modelfile"],
                          "the slot would run at Ollama's 4096 default")

    def test_num_ctx_is_a_project_key(self):
        self.p["num_ctx"] = 16384
        for c in self.create():
            self.assertIn("PARAMETER num_ctx 16384", c["modelfile"])

    def test_load_project_defaults_num_ctx(self):
        self.assertEqual(self.p["num_ctx"], 32768)

    def test_dry_run_shows_the_num_ctx_line(self):
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--create-slots", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("PARAMETER num_ctx 32768", out)
        self.assertNotIn("11", out.replace("11434", ""), "a seed may have been printed")


class TestUnreachableModelServer(SlotCase):

    def test_create_slots_stops_and_names_the_url(self):
        with mock.patch.object(runner, "model_server_reachable", return_value=False):
            with self.assertRaises(SystemExit) as e:
                runner.create_slots(self.p, False)
        msg = str(e.exception)
        self.assertIn("http://127.0.0.1:11434", msg, "the message did not name the URL tried")
        self.assertIn("ollama_host", msg)
        self.assertIn("Start Ollama", msg)

    def test_practice_stops_instead_of_printing_slots_ready(self):
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.make_test_suite("tests/public", {"basic": 1})
        argv = ["runner.py", "--project", self.path("project.json"),
                "--submission", self.path("submissions/ABC123456"),
                "--out", self.path("runs"), "--practice"]
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(runner, "model_server_reachable", return_value=False), \
             mock.patch.object(runner, "regenerate") as regenerated:
            with self.assertRaises(SystemExit) as e:
                runner.main()
        self.assertIn("http://127.0.0.1:11434", str(e.exception))
        self.assertFalse(regenerated.called, "the practice run carried on with no model server")


class TestVerifySlotsChecksNumCtx(SlotCase):

    def params(self, **over):
        base = {"temperature": "0.2", "seed": "11", "num_ctx": "32768"}
        base.update(over)
        return base

    def test_a_slot_without_num_ctx_is_a_problem(self):
        with mock.patch.object(runner, "slot_parameters",
                               side_effect=lambda p, i: {"temperature": str(p["temperatures"][i - 1]),
                                                         "seed": str([11, 22, 33][i - 1])}):
            problems = runner.verify_slots(self.p, [11, 22, 33])
        self.assertTrue(any("num_ctx" in x for x in problems), problems)

    def test_a_wrong_num_ctx_is_a_problem(self):
        with mock.patch.object(runner, "slot_parameters",
                               side_effect=lambda p, i: {"temperature": str(p["temperatures"][i - 1]),
                                                         "seed": str([11, 22, 33][i - 1]),
                                                         "num_ctx": "4096"}):
            problems = runner.verify_slots(self.p, [11, 22, 33])
        self.assertTrue(any("4096" in x for x in problems), problems)

    def test_correct_slots_report_no_problems(self):
        with mock.patch.object(runner, "slot_parameters",
                               side_effect=lambda p, i: {"temperature": str(p["temperatures"][i - 1]),
                                                         "seed": str([11, 22, 33][i - 1]),
                                                         "num_ctx": "32768"}):
            problems = runner.verify_slots(self.p, [11, 22, 33])
        self.assertEqual(problems, [])


# ------------------------------------------------------- 3. non-sandbox OpenCode baseURL

class TestOpenCodeBaseUrl(TempCase):

    P = {"ollama_host": "http://host.docker.internal:11434", "regeneration_timeout_s": 60}

    def base_url(self, p, sandbox):
        runner.write_opencode_config(p, self.dir, "ref-x-slot1", temperature=0.2, seed=7,
                                     sandbox=sandbox)
        cfg = json.load(open(os.path.join(self.dir, "opencode.json")))
        return cfg["provider"]["ollama"]["options"]["baseURL"]

    def test_the_sandbox_still_gets_the_container_name(self):
        self.assertEqual(self.base_url(dict(self.P), True),
                         "http://host.docker.internal:11434/v1")

    def test_a_host_run_gets_the_host_side_url(self):
        self.assertEqual(self.base_url(dict(self.P), False), "http://127.0.0.1:11434/v1",
                         "a practice run pointed OpenCode at a container-only name")

    def test_ollama_host_local_wins_on_the_host(self):
        p = dict(self.P, ollama_host_local="http://course-server.example:11434")
        self.assertEqual(self.base_url(p, False), "http://course-server.example:11434/v1")

    def test_regenerate_passes_the_sandbox_flag_through(self):
        p = runner.load_project(self.make_project(name="demo"))
        sub = self.path("submissions/ABC123456")
        self.write("submissions/ABC123456/SPEC.md", "build it")
        work = self.path("runs/ABC123456/practice-k1-work")
        os.makedirs(work, exist_ok=True)
        with mock.patch.object(runner, "sh", lambda *a, **k: (0, "", "", 0.1)):
            runner.regenerate(p, sub, work, 1, 7, "practice-k1", sandbox=False, dry=False)
        cfg = json.load(open(os.path.join(work, "opencode.json")))
        self.assertNotIn("host.docker.internal", cfg["provider"]["ollama"]["options"]["baseURL"])


# --------------------------------------------------------------- 4. missing binaries

class TestMissingBinaryDiagnostics(TempCase):

    def missing(self, exe):
        with mock.patch.object(runner.subprocess, "run", side_effect=FileNotFoundError(exe)):
            with self.assertRaises(SystemExit) as e:
                runner.sh([exe, "--version"])
        return str(e.exception)

    def test_missing_opencode_names_the_primer(self):
        msg = self.missing("opencode")
        self.assertEqual(msg, "opencode is not installed or not on PATH; "
                              "see templates/student-primer.md")

    def test_missing_docker_says_what_to_do(self):
        msg = self.missing("docker")
        self.assertIn("docker is not installed or not on PATH", msg)
        self.assertIn("--practice", msg)

    def test_a_missing_binary_never_reaches_the_student_as_a_traceback(self):
        p = runner.load_project(self.make_project(name="demo"))
        self.write("submissions/ABC123456/SPEC.md", "build it")
        work = self.path("runs/ABC123456/practice-k1-work")
        with mock.patch.object(runner.subprocess, "run", side_effect=FileNotFoundError("opencode")):
            with self.assertRaises(SystemExit) as e:
                runner.regenerate(p, self.path("submissions/ABC123456"), work, 1, 7,
                                  "practice-k1", sandbox=False, dry=False)
        self.assertIn("opencode is not installed", str(e.exception))

    def test_a_missing_docker_daemon_is_still_an_environment_failure(self):
        """The already-running-daemon case keeps its existing classification."""
        self.assertIsNotNone(runner.classify_failure(
            1, "", "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"))


# ------------------------------------------------------------------ 5. dry-run records

class TestDryRunRecords(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo")
        self.make_seeds()
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.make_test_suite("tests/hidden", {"basic": 1})
        self.p = runner.load_project(self.path("project.json"))

    def dry_batch(self):
        out = self.path("runs")
        runner.process_type_b(self.p, "ABC123456", self.path("submissions/ABC123456"), out,
                              [11, 22, 33], "practice", [1], None, False, True)
        return sorted(os.listdir(os.path.join(out, "ABC123456")))

    def test_dry_records_and_workdirs_are_named_apart(self):
        files = self.dry_batch()
        self.assertIn("practice-k1.dry.json", files, files)
        self.assertIn("practice-k1-dry-work", files, files)
        self.assertNotIn("practice-k1.json", files,
                         "a dry run wrote a file downstream tools would read as a run")
        self.assertNotIn("practice-k1-work", files)

    def test_a_dry_record_says_it_is_one(self):
        self.dry_batch()
        rec = json.load(open(self.path("runs/ABC123456/practice-k1.dry.json")))
        self.assertTrue(rec["dry_run"])
        self.assertFalse(rec["complete"])

    def test_the_opencode_config_stays_inside_the_dry_work_directory(self):
        self.dry_batch()
        self.assertTrue(os.path.exists(
            self.path("runs/ABC123456/practice-k1-dry-work/opencode.json")))

    def test_type_a_dry_records_are_named_apart_too(self):
        self.make_project(name="demo", ptype="A")
        p = runner.load_project(self.path("project.json"))
        self.make_solution("submissions/ABC123456")
        runner.process_type_a(p, "ABC123456", self.path("submissions/ABC123456"),
                              self.path("runs"), None, False, True)
        files = sorted(os.listdir(self.path("runs/ABC123456")))
        self.assertIn("a.dry.json", files, files)
        self.assertNotIn("a.json", files, files)

    def test_grade_py_ignores_a_dry_record(self):
        """A dry record must not be counted, not even as an incomplete slot."""
        self.perfect("ABC123456")
        self.write_json("runs/ABC123456/practice-k1.dry.json",
                        {"submission": "ABC123456", "type": "B", "slot": 1, "complete": False,
                         "dry_run": True, "tests": {"dry_run": True}})
        self.make_status([("ABC123456", "graded", 0, "")])
        _, gb, _ = run_tool("grade.py", "--project", self.path("project.json"),
                            "--runs", self.path("runs"), "--status", self.path("status.csv"),
                            expect_ok=True)
        row = parse_csv(gb)["ABC123456"]
        self.assertNotIn("never completed", row["note"],
                         "a --dry-run record was counted as an unfinished grading slot")

    def test_milestone_check_ignores_a_dry_record(self):
        os.makedirs(self.path("records"), exist_ok=True)
        self.write_json("records/practice-k1.dry.json", {"student_id": "ZZZ999999"})
        _, out, _ = run_tool("milestone.py", "check", "--project", self.path("project.json"),
                             "--records", self.path("records"))
        self.assertNotIn("ZZZ999999", out)


if __name__ == "__main__":
    unittest.main()

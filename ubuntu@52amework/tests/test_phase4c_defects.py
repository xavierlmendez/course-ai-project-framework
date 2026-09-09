"""Defects a second cold student walk found in the tools.

1. runner.py --practice checked for `opencode` last: it wrote seeds.practice.json,
   created three slot models and printed "slots ready" before failing.
2. ledger_server.py died with a raw OSError traceback when the port was busy.
3. A Type A milestone.json named a model that was never run.
4. milestone.py record defaulted --out to milestone.json, so two projects in one
   checkout overwrote each other's record.
"""
import json
import os
import socket
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from helpers import TempCase, run_tool, parse_csv  # noqa: E402
import ledger_server  # noqa: E402
import milestone  # noqa: E402
import runner  # noqa: E402


def which_without(*absent):
    """A shutil.which that finds every binary except the named ones."""
    return lambda name: None if os.path.basename(name) in absent else "/usr/bin/" + name


# ------------------------------------------------- 1. check the binaries first

class TestBinariesAreCheckedFirst(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo")            # type B
        self.write("submissions/ABC123456/SPEC.md", "build it")
        self.make_test_suite("tests/public", {"basic": 1})
        self.make_test_suite("tests/hidden", {"basic": 1})

    def practice_argv(self, *extra):
        return ["runner.py", "--project", self.path("project.json"),
                "--submission", self.path("submissions/ABC123456"),
                "--out", self.path("runs"), "--practice", *extra]

    def run_main(self, argv, absent):
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(runner.shutil, "which", side_effect=which_without(*absent)), \
             mock.patch.object(runner, "create_slots") as created, \
             mock.patch.object(runner, "model_server_reachable", return_value=True), \
             mock.patch.object(runner, "regenerate") as regenerated:
            with self.assertRaises(SystemExit) as e:
                runner.main()
        return e.exception, created, regenerated

    def test_practice_without_opencode_writes_nothing(self):
        exc, created, regenerated = self.run_main(self.practice_argv(), ["opencode"])
        self.assertEqual(str(exc), runner.MISSING_TOOL["opencode"])
        self.assertFalse(os.path.exists(self.path("seeds.practice.json")),
                         "a run that cannot happen wrote its seeds file anyway")
        self.assertFalse(created.called, "slot models were created for a run that cannot happen")
        self.assertFalse(regenerated.called)

    def test_the_missing_opencode_exit_status_is_one(self):
        """sys.exit(str) prints the sentence and exits 1; nothing prints 'slots ready'."""
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--submission", self.path("submissions/ABC123456"),
                                  "--out", self.path("runs"), "--practice",
                                  env_path="")
        self.assertEqual(code, 1, out + err)
        self.assertIn("opencode is not installed", err)
        self.assertNotIn("slots ready", out)
        self.assertFalse(os.path.exists(self.path("seeds.practice.json")))

    def test_a_sandboxed_run_checks_docker_first(self):
        self.make_seeds()
        argv = ["runner.py", "--project", self.path("project.json"),
                "--submission", self.path("submissions/ABC123456"),
                "--out", self.path("runs")]
        exc, _, regenerated = self.run_main(argv, ["docker"])
        self.assertIn("docker is not installed", str(exc))
        self.assertFalse(regenerated.called)

    def test_create_slots_checks_the_ollama_binary_before_writing(self):
        self.make_seeds()
        p = runner.load_project(self.path("project.json"))
        with mock.patch.object(runner.shutil, "which", side_effect=which_without("ollama")), \
             mock.patch.object(runner, "model_server_reachable", return_value=True), \
             mock.patch.object(runner, "sh") as shelled:
            with self.assertRaises(SystemExit) as e:
                runner.create_slots(p, False)
        self.assertEqual(str(e.exception), runner.MISSING_TOOL["ollama"])
        self.assertFalse(shelled.called, "ollama create ran with no ollama binary")

    def test_create_slots_checks_the_model_server_before_writing(self):
        self.make_seeds()
        p = runner.load_project(self.path("project.json"))
        with mock.patch.object(runner.shutil, "which", side_effect=which_without()), \
             mock.patch.object(runner, "model_server_reachable", return_value=False), \
             mock.patch.object(runner, "sh") as shelled:
            with self.assertRaises(SystemExit) as e:
                runner.create_slots(p, False)
        self.assertIn("cannot reach the model server", str(e.exception))
        self.assertFalse(shelled.called)


# ------------------------------------------------- 2. a busy port

class TestBusyPort(TempCase):

    def setUp(self):
        super().setUp()
        self.write("resource/index.md", "nonce {{NONCE}}\n")
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.addCleanup(self.sock.close)

    def serve(self, port):
        argv = ["ledger_server.py", "--resource", self.path("resource"),
                "--ledger", self.path("ledger.tsv"), "--nonce", "n1",
                "--bind", "127.0.0.1", "--port", str(port)]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as e:
                ledger_server.main()
        return e.exception

    def test_a_busy_port_is_one_sentence_not_a_traceback(self):
        msg = str(self.serve(self.port))
        self.assertIn(f"port {self.port} is already in use", msg)
        self.assertIn("another resource server is probably still running", msg)
        self.assertIn("--port", msg)
        self.assertNotIn("Traceback", msg)
        self.assertNotIn("Errno", msg)

    def test_the_project_port_is_the_one_named(self):
        """--port is absent, so the port comes from project.json's resource_port."""
        self.make_project(name="demo", resource_port=self.port)
        argv = ["ledger_server.py", "--project", self.path("project.json"),
                "--resource", self.path("resource"), "--ledger", self.path("ledger.tsv"),
                "--bind", "127.0.0.1"]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as e:
                ledger_server.main()
        self.assertIn(f"port {self.port} is already in use", str(e.exception))


# ------------------------------------------------- 3 & 4. the Type A milestone

class TypeACase(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo", ptype="A")
        self.make_test_suite("tests/public", {"basic": 2})
        self.solution = self.make_solution("submission")

    def record(self, *args, sid="ABC123456"):
        return run_tool("milestone.py", "record", "--project", self.path("project.json"),
                        "--solution", self.solution, "--student-id", sid, *args)


class TestTypeAClaimsNoModel(TypeACase):

    def test_the_record_names_no_model(self):
        code, out, err = self.record("--out", self.path("m.json"))
        self.assertEqual(code, 0, out + err)
        with open(self.path("m.json")) as fh:
            rec = json.load(fh)
        h = rec["harness"]
        self.assertTrue(h is None or h.get("model") is None,
                        f"a Type A record claims a model that was never run: {h}")
        self.assertNotIn("test-model", json.dumps(rec),
                         "the base model appears in a record for a project that runs no model")

    def test_check_accepts_a_type_a_record(self):
        os.makedirs(self.path("records"), exist_ok=True)
        code, out, err = self.record("--out", self.path("records/ABC123456.json"))
        self.assertEqual(code, 0, out + err)
        code, out, err = run_tool("milestone.py", "check", "--project", self.path("project.json"),
                                  "--records", self.path("records"))
        self.assertEqual(code, 0, err)
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["milestone"], "1", f"a valid Type A milestone was refused: {row}")

    def test_check_refuses_a_type_a_record_that_claims_a_model(self):
        os.makedirs(self.path("records"), exist_ok=True)
        path = self.path("records/ABC123456.json")
        self.record("--out", path)
        with open(path) as fh:
            rec = json.load(fh)
        rec["harness"] = {"type": "A", "model": "test-model"}
        rec["digest"] = milestone.digest_of(rec)
        with open(path, "w") as fh:
            json.dump(rec, fh)
        _, out, _ = run_tool("milestone.py", "check", "--project", self.path("project.json"),
                             "--records", self.path("records"))
        row = parse_csv(out)["ABC123456"]
        self.assertEqual(row["milestone"], "0")
        self.assertIn("run no harness", row["note"])

    def test_the_digest_still_covers_the_record(self):
        path = self.path("m.json")
        self.record("--out", path)
        with open(path) as fh:
            rec = json.load(fh)
        self.assertEqual(rec["digest"], milestone.digest_of(rec))
        rec["public"]["pass"] = 99
        self.assertNotEqual(rec["digest"], milestone.digest_of(rec))


class TestDefaultOutIsPerProject(TypeACase):

    def cwd_record(self, *args, sid="ABC123456"):
        """record with no --out, run from the project directory a student would be in."""
        here = os.getcwd()
        os.chdir(self.dir)
        try:
            return self.record(*args, sid=sid)
        finally:
            os.chdir(here)

    def test_the_default_is_named_after_the_project(self):
        code, out, err = self.cwd_record()
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.exists(self.path("milestone-demo.json")),
                        f"no milestone-demo.json; wrote {sorted(os.listdir(self.dir))}")
        self.assertFalse(os.path.exists(self.path("milestone.json")),
                         "two projects in one checkout would overwrite each other")
        self.assertIn("milestone-demo.json", out)

    def test_a_part_is_part_of_the_name(self):
        self.make_project(name="demo", ptype="A", part="p2")
        code, out, err = self.cwd_record()
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.exists(self.path("milestone-demo-p2.json")),
                        f"wrote {sorted(os.listdir(self.dir))}")

    def test_two_projects_do_not_collide(self):
        self.assertNotEqual(milestone.default_out_name({"name": "alpha"}),
                            milestone.default_out_name({"name": "beta"}))
        self.assertEqual(milestone.default_out_name({"name": "alpha"}), "milestone-alpha.json")
        self.assertEqual(milestone.default_out_name({"name": "alpha", "part": "2"}),
                         "milestone-alpha-2.json")

    def test_a_name_with_spaces_or_slashes_stays_one_file(self):
        self.assertEqual(milestone.default_out_name({"name": "cs 101/proj"}),
                         "milestone-cs-101-proj.json")

    def test_an_explicit_out_still_wins(self):
        code, out, err = self.cwd_record("--out", self.path("chosen.json"))
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.exists(self.path("chosen.json")))
        self.assertFalse(os.path.exists(self.path("milestone-demo.json")))


if __name__ == "__main__":
    unittest.main()

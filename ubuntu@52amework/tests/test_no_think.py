"""Slot Modelfiles disable qwen3's thinking mode (D-007).

A thinking model narrates its tool plan inside <think>, closes the block and ends the turn
with zero tool calls, so the agent loop never gets past the first step. `PARAMETER think
false` is rejected by Modelfiles and Ollama's /v1/chat/completions endpoint — the one
OpenCode uses — silently ignores `"think": false`, so the slot's TEMPLATE is the only
lever. Measured on the R620, 2026-09-09: docs/review/evidence/cpu-run/night6-4.txt.

Nothing here runs Ollama: `sh` is mocked and the base template comes from a fixture.
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, run_tool, qwen3_template, ROOT  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))
import runner  # noqa: E402


class TestNoThinkTemplate(unittest.TestCase):

    def setUp(self):
        self.base = qwen3_template()

    def test_the_fixture_is_a_thinking_template(self):
        self.assertIn(runner.NO_THINK_PATCH_A_OLD, self.base)
        self.assertIn(runner.NO_THINK_PATCH_B_OLD, self.base)

    def test_patch_a_appends_no_think_unconditionally(self):
        out = runner.no_think_template(self.base, "qwen3:14b")
        self.assertNotIn(runner.NO_THINK_PATCH_A_OLD, out)
        self.assertIn(runner.NO_THINK_PATCH_A_NEW, out)
        self.assertNotIn("/think\n", out, "the /think branch survived the patch")

    def test_patch_b_always_prefills_an_empty_think_block(self):
        out = runner.no_think_template(self.base, "qwen3:14b")
        self.assertNotIn(runner.NO_THINK_PATCH_B_OLD, out)
        self.assertIn("{{ if true -}}", out)
        self.assertIn("<think>", out)

    def test_the_patched_template_passes_the_slot_check(self):
        self.assertTrue(runner.slot_thinks(self.base))
        self.assertFalse(runner.slot_thinks(runner.no_think_template(self.base, "qwen3:14b")))

    def test_nothing_else_changes(self):
        out = runner.no_think_template(self.base, "qwen3:14b")
        undo = (out.replace(runner.NO_THINK_PATCH_A_NEW, runner.NO_THINK_PATCH_A_OLD)
                   .replace(runner.NO_THINK_PATCH_B_NEW, runner.NO_THINK_PATCH_B_OLD))
        self.assertEqual(undo, self.base)

    def test_a_missing_patch_a_anchor_names_the_model_and_the_way_out(self):
        broken = self.base.replace(runner.NO_THINK_PATCH_A_OLD, "{{- end }}")
        with self.assertRaises(SystemExit) as e:
            runner.no_think_template(broken, "llama3:8b")
        msg = str(e.exception)
        self.assertIn("llama3:8b", msg)
        self.assertIn("no thinking switch to disable", msg)
        self.assertIn('"thinking": "default"', msg)

    def test_a_missing_patch_b_anchor_is_also_refused(self):
        broken = self.base.replace(runner.NO_THINK_PATCH_B_OLD, "{{ if .Content -}}")
        with self.assertRaises(SystemExit) as e:
            runner.no_think_template(broken, "llama3:8b")
        self.assertIn("no thinking switch to disable", str(e.exception))

    def test_half_a_patch_is_not_silently_accepted(self):
        """Patch A alone leaves the model thinking; the tool must not claim otherwise."""
        half = self.base.replace(runner.NO_THINK_PATCH_B_OLD, "{{ if .Content -}}")
        with self.assertRaises(SystemExit):
            runner.no_think_template(half, "qwen3:14b")


class NoThinkSlotCase(TempCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo", base_model="qwen3:14b",
                          ollama_host="http://host.docker.internal:11434")
        self.make_seeds()
        self.p = runner.load_project(self.path("project.json"))

    def create(self, dry=False):
        """create_slots with the ollama CLI mocked; returns the calls it made."""
        calls = []

        def fake_sh(cmd, timeout=None, cwd=None, dry=False, env=None):
            if cmd[:3] == ["ollama", "show", "--template"]:
                calls.append({"cmd": cmd, "modelfile": ""})
                return 0, qwen3_template(), "", 0.0
            modelfile = open(cmd[-1]).read() if cmd[:2] == ["ollama", "create"] else ""
            calls.append({"cmd": cmd, "modelfile": modelfile})
            return 0, "", "", 0.0

        with mock.patch.object(runner, "sh", fake_sh), \
             mock.patch.object(runner.shutil, "which", side_effect=lambda x: "/usr/bin/" + x), \
             mock.patch.object(runner, "model_server_reachable", return_value=True):
            runner.create_slots(self.p, dry)
        return calls


class TestThinkingIsOffByDefault(NoThinkSlotCase):

    def test_load_project_defaults_thinking_off(self):
        self.assertEqual(self.p["thinking"], "off")

    def test_an_unknown_thinking_value_is_refused(self):
        self.make_project(name="demo", thinking="maybe")
        with self.assertRaises(SystemExit) as e:
            runner.load_project(self.path("project.json"))
        self.assertIn("thinking", str(e.exception))
        self.assertIn('"off"', str(e.exception))

    def test_the_base_template_is_read_once_for_all_three_slots(self):
        shows = [c for c in self.create() if c["cmd"][:3] == ["ollama", "show", "--template"]]
        self.assertEqual(len(shows), 1, shows)
        self.assertEqual(shows[0]["cmd"], ["ollama", "show", "--template", "qwen3:14b"])

    def test_every_slot_modelfile_carries_the_patched_template(self):
        creates = [c for c in self.create() if c["cmd"][:2] == ["ollama", "create"]]
        self.assertEqual(len(creates), 3, creates)
        want = runner.no_think_template(qwen3_template(), "qwen3:14b")
        for c in creates:
            mf = c["modelfile"]
            self.assertIn('TEMPLATE """' + want + '"""', mf)
            self.assertIn("FROM qwen3:14b", mf)
            self.assertIn("PARAMETER num_ctx 32768", mf)
            self.assertIn("PARAMETER temperature", mf)
            self.assertIn("PARAMETER seed", mf)
            self.assertFalse(runner.slot_thinks(mf), "the slot would still think")

    def test_the_parameter_lines_come_before_the_template(self):
        mf = [c for c in self.create() if c["cmd"][:2] == ["ollama", "create"]][0]["modelfile"]
        self.assertLess(mf.index("PARAMETER num_ctx"), mf.index("TEMPLATE"))

    def test_a_base_model_that_cannot_be_shown_is_an_environment_error(self):
        def fake_sh(cmd, timeout=None, cwd=None, dry=False, env=None):
            return 1, "", "model 'qwen3:14b' not found", 0.0

        with mock.patch.object(runner, "sh", fake_sh), \
             mock.patch.object(runner.shutil, "which", side_effect=lambda x: "/usr/bin/" + x), \
             mock.patch.object(runner, "model_server_reachable", return_value=True):
            with self.assertRaises(SystemExit) as e:
                runner.create_slots(self.p, False)
        msg = str(e.exception)
        self.assertIn("qwen3:14b", msg)
        self.assertIn("not found", msg)


class TestThinkingDefaultLeavesTheTemplateAlone(NoThinkSlotCase):

    def setUp(self):
        super().setUp()
        self.make_project(name="demo", base_model="qwen3:14b", thinking="default",
                          ollama_host="http://host.docker.internal:11434")
        self.p = runner.load_project(self.path("project.json"))

    def test_no_template_is_read_and_none_is_written(self):
        calls = self.create()
        self.assertEqual([c for c in calls if "show" in c["cmd"]], [])
        for c in calls:
            self.assertNotIn("TEMPLATE", c["modelfile"])

    def test_verify_slots_does_not_check_the_template(self):
        with mock.patch.object(runner, "slot_template",
                               side_effect=AssertionError("template was read")), \
             mock.patch.object(runner, "slot_parameters",
                               side_effect=lambda p, i: {"temperature": str(p["temperatures"][i - 1]),
                                                         "seed": str([11, 22, 33][i - 1]),
                                                         "num_ctx": "32768"}):
            self.assertEqual(runner.verify_slots(self.p, [11, 22, 33]), [])


class TestVerifySlotsRejectsAThinkingSlot(NoThinkSlotCase):

    def params(self, p, i):
        return {"temperature": str(p["temperatures"][i - 1]),
                "seed": str([11, 22, 33][i - 1]), "num_ctx": "32768"}

    def check(self, template):
        with mock.patch.object(runner, "slot_template", return_value=template), \
             mock.patch.object(runner, "slot_parameters", side_effect=self.params):
            return runner.verify_slots(self.p, [11, 22, 33])

    def test_a_stock_template_is_a_problem(self):
        problems = self.check(qwen3_template())
        self.assertEqual(len(problems), 3, problems)
        self.assertIn("slot 1 still thinks: re-run --create-slots", problems)

    def test_a_patched_template_is_no_problem(self):
        self.assertEqual(self.check(runner.no_think_template(qwen3_template(), "qwen3:14b")), [])

    def test_a_template_with_only_the_prefill_still_thinks(self):
        half = qwen3_template().replace(runner.NO_THINK_PATCH_B_OLD, runner.NO_THINK_PATCH_B_NEW)
        self.assertTrue(any("still thinks" in x for x in self.check(half)))

    def test_a_template_the_server_will_not_give_up_is_reported(self):
        with mock.patch.object(runner, "slot_template", side_effect=RuntimeError("boom")), \
             mock.patch.object(runner, "slot_parameters", side_effect=self.params):
            problems = runner.verify_slots(self.p, [11, 22, 33])
        self.assertTrue(any("could not read the template" in x for x in problems), problems)


class TestDryRun(NoThinkSlotCase):

    def dry_run(self, **project):
        self.make_project(name="demo", base_model="qwen3:14b",
                          ollama_host="http://host.docker.internal:11434", **project)
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--create-slots", "--dry-run")
        self.assertEqual(code, 0, err)
        return out

    def test_dry_run_names_the_patch_instead_of_printing_the_template(self):
        out = self.dry_run()
        self.assertIn("TEMPLATE: no-think (patched from qwen3:14b)", out)
        self.assertNotIn("$.IsThinkSet", out, "the whole template was printed")
        self.assertIn("PARAMETER num_ctx 32768", out)
        self.assertIn("PARAMETER seed <redacted>", out)

    def test_dry_run_with_thinking_default_says_nothing_about_templates(self):
        out = self.dry_run(thinking="default")
        self.assertNotIn("TEMPLATE", out)

    def test_dry_run_does_not_need_the_model_server(self):
        """No `ollama show` and no /api/tags: --dry-run works on a laptop with no server."""
        out = self.dry_run()
        self.assertIn("creating ref-demo-slot1", out)

    def test_the_shipped_examples_need_no_thinking_key(self):
        """Every example inherits the default, so its slots are created without thinking."""
        import glob
        import json
        found = glob.glob(os.path.join(ROOT, "examples", "*", "project.json"))
        found += glob.glob(os.path.join(ROOT, "examples", "*", "*", "project.json"))
        self.assertTrue(found)
        for path in found:
            with open(path) as fh:
                self.assertNotIn("thinking", json.load(fh), path)
            self.assertEqual(runner.load_project(path)["thinking"], "off", path)

    def test_a_shipped_example_prints_the_template_line(self):
        """The example's own project.json, run where seeds exist (they are never committed)."""
        import json
        with open(os.path.join(ROOT, "examples/02-astar-type-a/project.json")) as fh:
            proj = json.load(fh)
        self.write_json("project.json", proj)
        self.make_seeds()
        code, out, err = run_tool("runner.py", "--project", self.path("project.json"),
                                  "--create-slots", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("TEMPLATE: no-think (patched from qwen3:14b)", out)


if __name__ == "__main__":
    unittest.main()

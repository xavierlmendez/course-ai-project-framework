"""F-33: a handout a student is given must have nothing left to fill in.

The templates in templates/ are meant to carry `{{...}}`; a filled handout in
examples/ is what a student would actually read, so a placeholder there is a
question the student cannot answer. This test also guards the angle-bracket
form (`<INSTALL_URL>`), which the same review found in example 04.
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CURLY = re.compile(r"\{\{.*?\}\}")
# <SHOUTING> placeholders. Lowercase angle brackets ("<your dir>") are real prose.
ANGLE = re.compile(r"<[A-Z][A-Z0-9_]{2,}>")
# ...except inside a URL, where "http://<course-ollama-host>" is just as unusable.
URL_HOLE = re.compile(r"https?://\S*<(?!your\b)[^>]+>")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def hits(rx, text):
    return sorted(set(rx.findall(text)))


class TestFilledHandouts(unittest.TestCase):

    def example_handouts(self):
        paths = sorted(glob.glob(os.path.join(ROOT, "examples", "*", "handout.md")))
        self.assertTrue(paths, "no example handouts found")
        return paths

    def test_no_curly_placeholders_in_example_handouts(self):
        left = {}
        for path in self.example_handouts():
            found = hits(CURLY, read(path))
            if found:
                left[os.path.relpath(path, ROOT)] = found
        self.assertEqual(left, {}, f"unfilled placeholders in a student's handout: {left}")

    def test_no_shouting_angle_placeholders_in_example_handouts(self):
        left = {}
        for path in self.example_handouts():
            found = hits(ANGLE, read(path)) + hits(URL_HOLE, read(path))
            if found:
                left[os.path.relpath(path, ROOT)] = found
        self.assertEqual(left, {}, f"unfilled placeholders in a student's handout: {left}")

    def test_templates_are_readable_and_may_hold_placeholders(self):
        """The templates are the other half of the contract: they must still exist,
        and a handout template with no placeholder at all has been filled in place."""
        for name in ("handout-type-a.md", "handout-type-b.md"):
            path = os.path.join(ROOT, "templates", name)
            self.assertTrue(os.path.exists(path), path)
            self.assertTrue(CURLY.search(read(path)),
                            f"{name} has no placeholders left; a template was filled in place")

    def test_every_document_students_read_names_one_practice_command(self):
        """F-29: the practice command is `--practice`. No student-facing document may
        still show the flags it replaced."""
        paths = self.example_handouts() + [
            os.path.join(ROOT, "templates", "handout-type-b.md"),
            os.path.join(ROOT, "templates", "student-primer.md"),
        ]
        bad = {}
        for path in paths:
            text = read(path).replace("\\\n", " ")  # shell line continuations
            for line in text.splitlines():
                if "runner.py" not in line or "--create-slots" in line:
                    continue
                if "--practice" not in line:
                    bad.setdefault(os.path.relpath(path, ROOT), []).append(line.strip())
        self.assertEqual(bad, {}, f"a runner command students are shown is not the practice command: {bad}")


if __name__ == "__main__":
    unittest.main()

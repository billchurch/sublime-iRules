import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class PackageFilesTests(unittest.TestCase):
    def test_json_resources_parse(self):
        for pattern in ("*.sublime-commands", "*.sublime-menu", "Completions/*.sublime-completions"):
            for path in ROOT.glob(pattern):
                with self.subTest(path=path.name):
                    json.loads(path.read_text(encoding="utf-8"))

    def test_python_version_file_selects_modern_host(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.8")

    def test_syntax_header(self):
        text = (ROOT / "iRule.sublime-syntax").read_text(encoding="utf-8")
        head = text.split("contexts:")[0]
        self.assertIn("\nversion: 2\n", head)
        for extension in ("irul", "irule", "irules"):
            self.assertIn("\n  - %s\n" % extension, head)

    def test_snippets_are_sublime_snippets_with_unique_triggers(self):
        import xml.etree.ElementTree as ET
        snippets = sorted((ROOT / "Snippets").iterdir())
        self.assertEqual([p.name for p in snippets if p.suffix != ".sublime-snippet"], [])
        triggers = [ET.parse(str(p)).getroot().findtext("tabTrigger") for p in snippets]
        self.assertEqual(sorted(triggers), sorted(set(triggers)))

    def test_messages_json_points_at_existing_files(self):
        messages = json.loads((ROOT / "messages.json").read_text(encoding="utf-8"))
        self.assertIn("install", messages)
        for path in messages.values():
            self.assertTrue((ROOT / path).is_file(), path)

    def test_readme_has_no_links_into_other_branches(self):
        self.assertNotIn("../screenshots/", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_when_is_not_a_snippet(self):
        # `when` completes to the event list instead (see irules_plugin.py).
        import xml.etree.ElementTree as ET
        triggers = [
            ET.parse(str(p)).getroot().findtext("tabTrigger")
            for p in (ROOT / "Snippets").glob("*.sublime-snippet")
        ]
        self.assertNotIn("when", triggers)
        self.assertNotIn("whenp", triggers)

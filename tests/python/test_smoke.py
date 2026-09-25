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

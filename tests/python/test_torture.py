"""End-to-end formatter checks on a realistic, deliberately awkward iRule."""

import pathlib
import unittest

from irules_lib.formatter import format_irule

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class TortureTests(unittest.TestCase):
    def test_formatted_file_is_a_fixed_point(self):
        pretty = read("torture.irul")
        self.assertEqual(format_irule(pretty), pretty)

    def test_scrambled_indentation_is_restored_exactly(self):
        # torture-messy.irul is torture.irul with the indentation of every
        # code line scrambled; string and payload lines are left as they are.
        self.assertEqual(format_irule(read("torture-messy.irul")), read("torture.irul"))


if __name__ == "__main__":
    unittest.main()

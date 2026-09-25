import unittest

from tests.python.irules_data_helpers import snapshot
from tools.irules_data.build import DataError, build_database


class BuildTests(unittest.TestCase):
    def test_merges_upstream_with_additions_and_deprecations(self):
        db = build_database(
            snapshot(["HTTP::uri", "matchclass"], ["HTTP_REQUEST"], {"HTTP::uri": "9.0.0"}),
            {
                "commands": {"add": {"PSM::FTP::enable": {}}, "deprecate": ["matchclass"]},
                "events": {"add": {"TDS_REQUEST": {"description": "tds"}}},
            },
        )
        self.assertEqual(list(db["commands"]), ["HTTP::uri", "PSM::FTP::enable", "matchclass"])
        self.assertEqual(db["commands"]["HTTP::uri"]["since"], "9.0.0")
        self.assertTrue(db["commands"]["matchclass"]["deprecated"])
        self.assertEqual(db["events"]["TDS_REQUEST"]["description"], "tds")

    def test_exclude_and_rename(self):
        db = build_database(
            snapshot(["Operators", "GTP::header extension"]),
            {"commands": {"exclude": ["Operators"], "rename": {"GTP::header extension": "GTP::header"}}},
        )
        self.assertEqual(list(db["commands"]), ["GTP::header"])

    def test_invalid_upstream_name_is_an_error_not_a_silent_drop(self):
        with self.assertRaisesRegex(DataError, "connect info"):
            build_database(snapshot(["connect info"]), {})

    def test_addition_that_is_now_documented_is_an_error(self):
        with self.assertRaisesRegex(DataError, "now documented upstream"):
            build_database(snapshot(["TAP::score"]), {"commands": {"add": {"TAP::score": {}}}})

    def test_deprecating_unknown_name_is_an_error(self):
        with self.assertRaisesRegex(DataError, "unknown name"):
            build_database(snapshot(), {"commands": {"deprecate": ["nope"]}})



if __name__ == "__main__":
    unittest.main()


class SnapshotShrinkTests(unittest.TestCase):
    def test_large_drop_in_entries_is_an_error(self):
        from tools.irules_data.build import check_snapshot_size
        old = snapshot(["A::%d" % i for i in range(100)], ["E_%d" % i for i in range(10)])
        new = snapshot(["A::%d" % i for i in range(50)], ["E_%d" % i for i in range(10)])
        with self.assertRaisesRegex(DataError, "commands: 50 entries, previously 100"):
            check_snapshot_size(old, new)

    def test_small_changes_are_fine(self):
        from tools.irules_data.build import check_snapshot_size
        old = snapshot(["A::%d" % i for i in range(100)], ["E_%d" % i for i in range(10)])
        new = snapshot(["A::%d" % i for i in range(95)], ["E_%d" % i for i in range(11)])
        check_snapshot_size(old, new)
        check_snapshot_size({}, new)

import unittest

from irules_lib.context import completing_event_name, map_column


class CompletingEventNameTests(unittest.TestCase):
    def test_true_right_after_when(self):
        for prefix in ("when ", "when HTTP_RE", "    when\tCLIENT"):
            self.assertTrue(completing_event_name(prefix), prefix)

    def test_false_elsewhere(self):
        for prefix in ("when", "whenever ", "when HTTP_REQUEST ", "set when ", "# when ", "log when X"):
            self.assertFalse(completing_event_name(prefix), prefix)


class MapColumnTests(unittest.TestCase):
    def test_column_after_indent_moves_with_the_text(self):
        self.assertEqual(map_column(6, "  pool a", "    pool a"), 8)
        self.assertEqual(map_column(8, "      pool a", "    pool a"), 6)

    def test_column_inside_old_indent_stays_inside_new_indent(self):
        self.assertEqual(map_column(1, "  pool a", "pool a"), 0)
        self.assertEqual(map_column(1, "  pool a", "    pool a"), 1)


if __name__ == "__main__":
    unittest.main()

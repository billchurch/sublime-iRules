import unittest

from irules_lib.context import (
    OPEN_EVENT_LIST,
    SPACE_THEN_EVENT_LIST,
    after_text_command,
    completing_event_name,
    event_completion,
    map_column,
)


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


class EventCompletionTests(unittest.TestCase):
    def test_end_of_line_expands_to_priority_and_body(self):
        self.assertEqual(
            event_completion("HTTP_REQUEST", ""),
            ("HTTP_REQUEST priority ${1:500} {\n\t$0\n}", True),
        )

    def test_trailing_whitespace_still_counts_as_end_of_line(self):
        self.assertTrue(event_completion("HTTP_REQUEST", "   ")[1])

    def test_existing_text_after_caret_inserts_only_the_name(self):
        self.assertEqual(event_completion("HTTP_REQUEST", " priority 100 {"), ("HTTP_REQUEST", False))
        self.assertEqual(event_completion("HTTP_REQUEST", " {"), ("HTTP_REQUEST", False))


class AfterTextCommandTests(unittest.TestCase):
    def test_completing_when_adds_space_and_opens_event_list(self):
        for command in ("commit_completion", "insert_best_completion", "insert_completion"):
            self.assertEqual(after_text_command(command, {}, "    when"), SPACE_THEN_EVENT_LIST, command)

    def test_typing_space_after_when_opens_event_list(self):
        self.assertEqual(after_text_command("insert", {"characters": " "}, "when "), OPEN_EVENT_LIST)

    def test_nothing_elsewhere(self):
        cases = [
            ("insert", {"characters": " "}, "set when "),
            ("insert", {"characters": " "}, "when HTTP_REQUEST "),
            ("insert", {"characters": "n"}, "when"),
            ("commit_completion", {}, "whenever"),
            ("left_delete", {}, "when "),
        ]
        for command, args, prefix in cases:
            self.assertIsNone(after_text_command(command, args, prefix), (command, prefix))


if __name__ == "__main__":
    unittest.main()

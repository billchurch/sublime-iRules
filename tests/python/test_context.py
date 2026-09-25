import unittest

from irules_lib.context import completing_event_name


class CompletingEventNameTests(unittest.TestCase):
    def test_true_right_after_when(self):
        for prefix in ("when ", "when HTTP_RE", "    when\tCLIENT"):
            self.assertTrue(completing_event_name(prefix), prefix)

    def test_false_elsewhere(self):
        for prefix in ("when", "whenever ", "when HTTP_REQUEST ", "set when ", "# when ", "log when X"):
            self.assertFalse(completing_event_name(prefix), prefix)


if __name__ == "__main__":
    unittest.main()

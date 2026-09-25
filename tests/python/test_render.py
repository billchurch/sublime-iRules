import json
import unittest

from tests.python.irules_data_helpers import snapshot
from tools.irules_data.build import DataError, build_database
from tools.irules_data.render import (
    alternation,
    snippet_triggers,
    details,
    render_completions,
    render_events_module,
    render_syntax,
    syntax_lists,
    tcl_names,
)

SYNTAX = """variables:
  most_likely_tcl_code: 'set|append'
  most_likely_tcl_control_code: 'if|while'
  most_likely_irule_code: 'old'
  most_likely_irule_nscode: 'OLD::x'
  most_likely_irule_events: 'OLD_EVENT'
  deprecated_irule_code: 'old_dep'
  deprecated_irule_events: 'OLD_DEP'
  disabled_tcl_code: 'exec'
"""



class RenderTests(unittest.TestCase):
    def setUp(self):
        self.db = build_database(
            snapshot(
                ["HTTP::uri", "LSN::inbound", "LSN::inbound-entry", "pool", "if", ("matchclass", True)],
                ["HTTP_REQUEST", ("AUTH_ERROR", True)],
                {"HTTP::uri": "9.0.0"},
            ),
            {},
        )

    def test_alternation_puts_longer_names_first(self):
        self.assertEqual(alternation(["LSN::inbound", "LSN::inbound-entry", "a"]), "LSN::inbound-entry|LSN::inbound|a")

    def test_syntax_variables_are_replaced_and_tcl_lists_kept(self):
        skip = {"if"} | tcl_names(SYNTAX)
        text = render_syntax(SYNTAX, syntax_lists(self.db, skip))
        self.assertIn("  most_likely_irule_code: 'pool'\n", text)
        self.assertIn("  most_likely_irule_nscode: 'LSN::inbound-entry|LSN::inbound|HTTP::uri'\n", text)
        self.assertIn("  most_likely_irule_events: 'HTTP_REQUEST'\n", text)
        self.assertIn("  deprecated_irule_code: 'matchclass'\n", text)
        self.assertIn("  deprecated_irule_events: 'AUTH_ERROR'\n", text)
        self.assertIn("  most_likely_tcl_code: 'set|append'\n", text)

    def test_missing_syntax_variable_is_an_error(self):
        with self.assertRaisesRegex(DataError, "most_likely_irule_code"):
            render_syntax("variables:\n", syntax_lists(self.db, set()))

    def test_details_escape_html_and_link_docs(self):
        text = details({"description": "a <b> & c", "url": "https://x/y.html", "since": "9.0.0", "deprecated": False})
        self.assertEqual(text, 'a &lt;b&gt; &amp; c — BIG-IP 9.0.0+ — <a href="https://x/y.html">docs</a>')

    def test_details_truncates_long_descriptions(self):
        text = details({"description": "x" * 500, "url": None, "since": None, "deprecated": False})
        self.assertEqual(len(text), 160)
        self.assertTrue(text.endswith("…"))

    def test_completions_mark_deprecated_and_include_tcl_and_extras(self):
        doc = json.loads(render_completions(self.db, {
            "tcl_completions": ["set", "pool"],
            "completions_extra": [{"trigger": "class match", "contents": "class match -- $0"}],
        }))
        by_trigger = {item["trigger"]: item for item in doc["completions"]}
        self.assertEqual(by_trigger["HTTP::uri"]["annotation"], "HTTP")
        self.assertEqual(by_trigger["matchclass"]["kind"], ["function", "d", "Deprecated"])
        self.assertEqual(by_trigger["set"]["kind"], "keyword")
        self.assertEqual(by_trigger["pool"]["annotation"], "iRule")  # not duplicated as Tcl
        self.assertIn("class match", by_trigger)
        self.assertEqual(len(doc["completions"]), len(by_trigger))

    def test_extra_completion_replaces_generated_one_and_keeps_its_details(self):
        doc = json.loads(render_completions(self.db, {
            "completions_extra": [{"trigger": "pool", "contents": "pool $0"}],
        }))
        pools = [item for item in doc["completions"] if item["trigger"] == "pool"]
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0]["contents"], "pool $0")
        self.assertEqual(pools[0]["annotation"], "iRule")

    def test_triggers_provided_by_snippets_are_left_out(self):
        doc = json.loads(render_completions(
            self.db,
            {"tcl_completions": ["set"], "completions_extra": [{"trigger": "set", "contents": "set $0"}]},
            skip_triggers={"pool", "set"},
        ))
        triggers = {item["trigger"] for item in doc["completions"]}
        self.assertNotIn("pool", triggers)
        self.assertNotIn("set", triggers)
        self.assertIn("HTTP::uri", triggers)

    def test_snippet_triggers_reads_tab_triggers(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "a.sublime-snippet").write_text(
                "<snippet><content>x</content><tabTrigger>when</tabTrigger></snippet>", encoding="utf-8")
            Path(folder, "notes.txt").write_text("ignored", encoding="utf-8")
            self.assertEqual(snippet_triggers(Path(folder)), {"when"})

    def test_events_module_is_valid_python(self):
        namespace = {}
        exec(render_events_module(self.db), namespace)
        self.assertEqual(
            namespace["EVENTS"][1],
            ("HTTP_REQUEST", 'http_request \u2014 <a href="u/HTTP_REQUEST">docs</a>', False),
        )



if __name__ == "__main__":
    unittest.main()


class PrefixConflictTests(unittest.TestCase):
    def test_earlier_list_name_that_is_a_prefix_of_a_later_one_is_an_error(self):
        # command-name matches deprecated names before valid ones, so a
        # deprecated LSN::inbound would highlight only part of LSN::inbound-entry.
        database = build_database(
            snapshot(["pool", ("LSN::inbound", True), "LSN::inbound-entry"], ["HTTP_REQUEST", ("AUTH_ERROR", True)]),
            {},
        )
        with self.assertRaisesRegex(DataError, "LSN::inbound.*LSN::inbound-entry"):
            render_syntax(SYNTAX, syntax_lists(database, set()))

    def test_word_continuations_are_not_conflicts(self):
        database = build_database(
            snapshot(["pool", ("HTTP::cla", True), "HTTP::class"], ["HTTP_REQUEST", ("HTTP_REQ", True)]),
            {},
        )
        render_syntax(SYNTAX, syntax_lists(database, set()))


class EmptyListTests(unittest.TestCase):
    def test_empty_generated_list_is_an_error_not_an_empty_regex(self):
        database = build_database(snapshot(["HTTP::uri", "pool", ("matchclass", True)], []), {})
        with self.assertRaisesRegex(DataError, "most_likely_irule_events"):
            render_syntax(SYNTAX, syntax_lists(database, set()))

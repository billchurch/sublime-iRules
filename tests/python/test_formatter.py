import unittest

from irules_lib.formatter import format_irule


def fmt(source, **kwargs):
    return format_irule("\n".join(source), **kwargs).split("\n")


class FormatIruleTests(unittest.TestCase):
    def test_indents_when_body(self):
        self.assertEqual(
            fmt(["when HTTP_REQUEST {", "log local0. hi", "}"]),
            ["when HTTP_REQUEST {", "    log local0. hi", "}"],
        )

    def test_nested_blocks_and_else(self):
        self.assertEqual(
            fmt([
                "when HTTP_REQUEST {",
                "if { $a } {",
                "pool a",
                "} elseif { $b } {",
                "pool b",
                "} else {",
                "drop",
                "}",
                "}",
            ]),
            [
                "when HTTP_REQUEST {",
                "    if { $a } {",
                "        pool a",
                "    } elseif { $b } {",
                "        pool b",
                "    } else {",
                "        drop",
                "    }",
                "}",
            ],
        )

    def test_single_line_block_does_not_change_depth(self):
        # Regression: the old formatter dedented after any line ending in "}".
        self.assertEqual(
            fmt(["when X {", "if {$a} { set x 1 }", "log local0. after", "}"]),
            ["when X {", "    if {$a} { set x 1 }", "    log local0. after", "}"],
        )

    def test_continuation_lines_get_one_extra_level(self):
        self.assertEqual(
            fmt(["when X {", 'log local0. "a" \\', '"b"', "pool p", "}"]),
            ["when X {", '    log local0. "a" \\', '        "b"', "    pool p", "}"],
        )

    def test_bracketed_list_across_continuations(self):
        self.assertEqual(
            fmt(["when X {", "set l [list \\", "a \\", "b \\", "]", "}"]),
            ["when X {", "    set l [list \\", "        a \\", "        b \\", "    ]", "}"],
        )

    def test_escaped_braces_are_ignored(self):
        self.assertEqual(
            fmt(["when X {", 'set s "\\{"', "pool p", "}"]),
            ["when X {", '    set s "\\{"', "    pool p", "}"],
        )

    def test_top_level_comment_braces_are_ignored(self):
        self.assertEqual(
            fmt(["# a comment with a brace {", "when X {", "pool p", "}"]),
            ["# a comment with a brace {", "when X {", "    pool p", "}"],
        )

    def test_multiline_string_is_left_verbatim(self):
        self.assertEqual(
            fmt(["when X {", 'HTTP::respond 200 content "line one', "   keep  this spacing", '"', "pool p", "}"]),
            ["when X {", '    HTTP::respond 200 content "line one', "   keep  this spacing", '"', "    pool p", "}"],
        )

    def test_quote_inside_braced_word_does_not_open_string(self):
        self.assertEqual(
            fmt(["when X {", 'set q {"}', "pool p", "}"]),
            ["when X {", '    set q {"}', "    pool p", "}"],
        )

    def test_blank_lines_and_trailing_whitespace_are_cleaned(self):
        self.assertEqual(
            fmt(["when X {   ", "", "   pool p   ", "}", ""]),
            ["when X {", "", "    pool p", "}", ""],
        )

    def test_custom_indent_and_base_indent(self):
        self.assertEqual(
            fmt(["if {$a} {", "pool p", "}"], indent="\t", base_indent="    "),
            ["    if {$a} {", "    \tpool p", "    }"],
        )

    def test_unbalanced_closers_never_go_negative(self):
        self.assertEqual(fmt(["}", "}", "pool p"]), ["}", "}", "pool p"])

    def test_quotes_inside_command_substitution_do_not_end_the_string(self):
        source = [
            "when X {",
            'HTTP::respond 200 content "<html>[HTTP::header "Host"]',
            "  <pre>",
            "    keep",
            "  </pre>",
            '</html>"',
            "pool p",
            "}",
        ]
        expected = ["when X {", "    " + source[1]] + source[2:6] + ["    pool p", "}"]
        self.assertEqual(fmt(source), expected)

    def test_balanced_nested_quotes_do_not_leave_a_string_open(self):
        self.assertEqual(
            fmt(["when X {", 'log local0. "UA: [HTTP::header "User-Agent"] "', "pool p", "}"]),
            ["when X {", '    log local0. "UA: [HTTP::header "User-Agent"] "', "    pool p", "}"],
        )

    def test_trailing_spaces_inside_an_open_string_are_kept(self):
        self.assertEqual(
            fmt(["when X {", 'HTTP::respond 200 content "a   ', 'b"', "}"]),
            ["when X {", '    HTTP::respond 200 content "a   ', 'b"', "}"],
        )

    def test_braced_payload_that_starts_on_the_same_line_is_left_verbatim(self):
        source = [
            "when X {",
            "HTTP::respond 200 content {<html>",
            "  <pre>",
            "    keep",
            "  </pre>",
            "</html>}",
            "pool p",
            "}",
        ]
        expected = ["when X {", "    " + source[1]] + source[2:6] + ["    pool p", "}"]
        self.assertEqual(fmt(source), expected)

    def test_brackets_inside_braced_words_do_not_change_depth(self):
        self.assertEqual(
            fmt(["when X {", "if {[regexp {^[^]]+} $x]} {", "pool a", "}", "pool b", "}"]),
            ["when X {", "    if {[regexp {^[^]]+} $x]} {", "        pool a", "    }", "    pool b", "}"],
        )

    def test_lone_quote_inside_braced_word_does_not_open_a_string(self):
        self.assertEqual(
            fmt(["when X {", 'set q { " }', "pool p", "}"]),
            ["when X {", '    set q { " }', "    pool p", "}"],
        )

    def test_top_level_inline_comment_braces_are_ignored(self):
        self.assertEqual(
            fmt(["set x 1 ;# {", "when X {", "pool p", "}"]),
            ["set x 1 ;# {", "when X {", "    pool p", "}"],
        )

    def test_outdent_lets_a_selection_close_an_enclosing_block(self):
        self.assertEqual(
            fmt(["pool a", "pool b", "}"], base_indent="    ", outdent=True),
            ["    pool a", "    pool b", "}"],
        )

    def test_outdent_selection_starting_with_else(self):
        self.assertEqual(
            fmt(["} else {", "pool b", "}"], base_indent="    ", outdent=True),
            ["    } else {", "        pool b", "    }"],
        )

    def test_formatting_is_idempotent(self):
        source = "\n".join([
            "when HTTP_REQUEST priority 100 {",
            "switch -glob -- [HTTP::uri] {",
            '"/api*" {',
            "pool api",
            "}",
            "default {",
            "pool web",
            "}",
            "}",
            "}",
            "",
        ])
        once = format_irule(source)
        self.assertEqual(format_irule(once), once)


if __name__ == "__main__":
    unittest.main()

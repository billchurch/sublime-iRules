"""Tests for irules_plugin.py against a minimal fake of the Sublime Text API."""

import importlib
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Region(object):
    def __init__(self, a, b=None):
        self.a = a
        self.b = a if b is None else b

    def begin(self):
        return min(self.a, self.b)

    def end(self):
        return max(self.a, self.b)

    def empty(self):
        return self.a == self.b

    def size(self):
        return self.end() - self.begin()

    def cover(self, other):
        return Region(min(self.begin(), other.begin()), max(self.end(), other.end()))

    def __eq__(self, other):
        return (self.a, self.b) == (other.a, other.b)

    def __repr__(self):
        return "Region(%d, %d)" % (self.a, self.b)


class Selection(list):
    def add(self, region):
        self.append(region if isinstance(region, Region) else Region(region))


class CompletionItem(object):
    def __init__(self, trigger, annotation="", completion="", completion_format=0, kind=None, details=""):
        self.trigger = trigger
        self.completion = completion or trigger
        self.completion_format = completion_format
        self.annotation = annotation
        self.kind = kind
        self.details = details


class CompletionList(object):
    def __init__(self, completions=None, flags=0):
        self.completions = completions
        self.flags = flags


class FakeView(object):
    def __init__(self, text, selections, tab_size=4):
        self.text = text
        self._sel = Selection(selections)
        self._settings = {"translate_tabs_to_spaces": True, "tab_size": tab_size}
        self.viewport_moves = 0
        self.commands = []
        self.listener = None

    def syntax(self):
        return types.SimpleNamespace(scope="source.irule")

    def settings(self):
        return self._settings

    def sel(self):
        return self._sel

    def size(self):
        return len(self.text)

    def substr(self, region):
        return self.text[region.begin():region.end()]

    def replace(self, edit, region, text):
        self.text = self.text[:region.begin()] + text + self.text[region.end():]

    def rowcol(self, point):
        before = self.text[:point]
        return before.count("\n"), len(before) - (before.rfind("\n") + 1)

    def text_point(self, row, col):
        lines = self.text.split("\n")
        return sum(len(line) + 1 for line in lines[:row]) + col

    def line(self, region):
        if not isinstance(region, Region):
            region = Region(region)
        begin = self.text.rfind("\n", 0, region.begin()) + 1
        end = self.text.find("\n", region.end())
        return Region(begin, len(self.text) if end == -1 else end)

    def run_command(self, name, args=None):
        self.commands.append((name, args or {}))
        if name == "insert":
            point = self._sel[0].b
            self.text = self.text[:point] + args["characters"] + self.text[point:]
            self._sel[:] = [Region(point + len(args["characters"]))]
        # Sublime notifies listeners about commands that plugins run, too.
        if self.listener is not None:
            self.listener.on_post_text_command(self, name, args or {})

    def viewport_position(self):
        return (0.0, 0.0)

    def set_viewport_position(self, position, animate=True):
        self.viewport_moves += 1


def load_plugin():
    sublime = types.ModuleType("sublime")
    sublime.Region = Region
    sublime.KIND_ID_FUNCTION = 1
    sublime.KIND_ID_COLOR_REDISH = 2
    sublime.INHIBIT_WORD_COMPLETIONS = 8
    sublime.INHIBIT_EXPLICIT_COMPLETIONS = 16
    sublime.COMPLETION_FORMAT_TEXT = 0
    sublime.COMPLETION_FORMAT_SNIPPET = 1
    sublime.CompletionItem = CompletionItem
    sublime.CompletionList = CompletionList
    sublime.load_settings = lambda name: {}
    sublime_plugin = types.ModuleType("sublime_plugin")
    for name in ("TextCommand", "WindowCommand", "EventListener"):
        setattr(sublime_plugin, name, type(name, (object,), {"__init__": lambda self, view=None: setattr(self, "view", view)}))
    sys.modules["sublime"] = sublime
    sys.modules["sublime_plugin"] = sublime_plugin
    package = types.ModuleType("irules_pkg")
    package.__path__ = [str(ROOT)]
    sys.modules["irules_pkg"] = package
    return importlib.import_module("irules_pkg.irules_plugin")


PLUGIN = load_plugin()


def run_format(text, selections, whole_file=False):
    view = FakeView(text, selections)
    PLUGIN.FormatIruleCommand(view).run(None, whole_file=whole_file)
    return view


class FormatCommandTests(unittest.TestCase):
    def test_selection_ending_at_column_zero_does_not_pull_in_the_next_line(self):
        text = "when X {\n    pool a\n    pool b\n}\n"
        start, end = text.index("    pool a"), text.index("}")
        view = run_format(text, [Region(start, end)])
        self.assertEqual(view.text, text)

    def test_selection_that_includes_the_closing_brace_outdents_it(self):
        text = "when X {\n  pool a\n  pool b\n}\n"
        start, end = text.index("  pool a"), text.index("}") + 1
        view = run_format(text, [Region(start, end)])
        self.assertEqual(view.text, "when X {\n  pool a\n  pool b\n}\n")

    def test_unchanged_text_keeps_selections_and_viewport(self):
        text = "when X {\n    pool a\n}\n"
        selection = Region(13, 17)
        view = run_format(text, [selection], whole_file=True)
        self.assertEqual(list(view.sel()), [selection])
        self.assertEqual(view.viewport_moves, 0)

    def test_selection_and_caret_follow_the_text_when_reindented(self):
        text = "when X {\npool a\n}\n"
        start = text.index("pool")
        view = run_format(text, [Region(start, start + 4)], whole_file=True)
        self.assertEqual(view.text, "when X {\n    pool a\n}\n")
        selected = view.sel()[0]
        self.assertEqual(view.substr(selected), "pool")


def complete(text, point):
    view = FakeView(text, [Region(point)])
    return PLUGIN.IruleListener().on_query_completions(view, "", [point])


class EventCompletionTests(unittest.TestCase):
    def test_event_at_end_of_line_expands_to_priority_snippet(self):
        text = "when HTTP_RE"
        result = complete(text, len(text))
        item = next(i for i in result.completions if i.trigger == "HTTP_REQUEST")
        self.assertEqual(item.completion, "HTTP_REQUEST priority ${1:500} {\n\t$0\n}")
        self.assertEqual(item.completion_format, 1)

    def test_event_with_text_after_caret_inserts_name_only(self):
        text = "when HTTP_RE priority 100 {"
        result = complete(text, len("when HTTP_RE"))
        item = next(i for i in result.completions if i.trigger == "HTTP_REQUEST")
        self.assertEqual(item.completion, "HTTP_REQUEST")
        self.assertEqual(item.completion_format, 0)

    def test_no_event_completions_outside_when(self):
        text = "pool HTTP_RE"
        self.assertIsNone(complete(text, len(text)))


class WhenOpensEventListTests(unittest.TestCase):
    def after(self, text, command, args=None):
        view = FakeView(text, [Region(len(text))])
        view.listener = PLUGIN.IruleListener()
        view.listener.on_post_text_command(view, command, args or {})
        return view

    def test_completing_when_inserts_space_and_opens_event_completions(self):
        view = self.after("when", "commit_completion")
        self.assertEqual(view.text, "when ")
        self.assertEqual([name for name, _ in view.commands], ["insert", "auto_complete"])
        self.assertTrue(view.commands[1][1].get("api_completions_only"))

    def test_typing_space_after_when_opens_event_completions(self):
        view = self.after("    when ", "insert", {"characters": " "})
        self.assertEqual([name for name, _ in view.commands], ["auto_complete"])

    def test_other_lines_are_left_alone(self):
        view = self.after("set when ", "insert", {"characters": " "})
        self.assertEqual(view.commands, [])


if __name__ == "__main__":
    unittest.main()

"""Sublime Text commands and listeners for the iRules package."""

import re
import sys

import sublime
import sublime_plugin

# When the package is updated, Sublime reloads this module but keeps the
# irules_lib modules it imported earlier. Drop them so the new versions are
# imported too; otherwise a stale module can break the import below.
for _name in [name for name in sys.modules if name.startswith(__package__ + ".irules_lib")]:
    del sys.modules[_name]

from .irules_lib.context import (
    completing_event_name,
    event_completion,
    map_column,
    should_open_event_list,
)
from .irules_lib.events import EVENTS
from .irules_lib.formatter import format_irule

SETTINGS_FILE = "iRules.sublime-settings"
SYNTAX_SCOPE = "source.irule"
LEADING_WHITESPACE_RE = re.compile(r"[ \t]*")

KIND_EVENT = (sublime.KIND_ID_FUNCTION, "e", "Event")
KIND_DEPRECATED_EVENT = (sublime.KIND_ID_COLOR_REDISH, "d", "Deprecated event")


def is_irule(view):
    syntax = view.syntax()
    return syntax is not None and syntax.scope == SYNTAX_SCOPE


def indent_unit(view):
    settings = view.settings()
    if settings.get("translate_tabs_to_spaces", False):
        return " " * int(settings.get("tab_size", 4))
    return "\t"


def _format_targets(view, whole_file):
    """[(region, base_indent, outdent)] to format, merged so no two overlap."""
    selections = [region for region in view.sel() if not region.empty()]
    if whole_file or not selections:
        return [(sublime.Region(0, view.size()), "", False)]
    targets = []
    for region in selections:
        begin, end = region.begin(), region.end()
        # A selection made with shift+down ends at column 0 of the next
        # line; that line is not part of it.
        if view.rowcol(end)[1] == 0 and view.rowcol(begin)[0] != view.rowcol(end)[0]:
            end -= 1
        lines = view.line(sublime.Region(begin, end))
        if targets and targets[-1][0].end() >= lines.begin():
            targets[-1] = (targets[-1][0].cover(lines), targets[-1][1], True)
            continue
        base = LEADING_WHITESPACE_RE.match(view.substr(lines)).group(0)
        targets.append((lines, base, True))
    return targets


def _line_text(view, row):
    return view.substr(view.line(view.text_point(row, 0)))


class IruleFormatCommand(sublime_plugin.TextCommand):
    """Re-indent the selected lines, or the whole file when nothing is selected."""

    def is_enabled(self, whole_file=False):
        return is_irule(self.view)

    def is_visible(self, whole_file=False):
        return is_irule(self.view)

    def run(self, edit, whole_file=False):
        view = self.view
        indent = indent_unit(view)
        # The formatter never adds or removes lines, so rows stay valid.
        ends = [(view.rowcol(region.a), view.rowcol(region.b)) for region in view.sel()]
        rows = {row for pair in ends for row, _ in pair}
        old_lines = {row: _line_text(view, row) for row in rows}
        viewport = view.viewport_position()
        changed = False
        # Replace from the end so earlier regions keep their offsets.
        for region, base, outdent in reversed(_format_targets(view, whole_file)):
            original = view.substr(region)
            formatted = format_irule(original, indent=indent, base_indent=base, outdent=outdent)
            if formatted != original:
                view.replace(edit, region, formatted)
                changed = True
        if not changed:
            return
        view.sel().clear()
        for (a_row, a_col), (b_row, b_col) in ends:
            view.sel().add(
                sublime.Region(
                    self._point(a_row, a_col, old_lines[a_row]),
                    self._point(b_row, b_col, old_lines[b_row]),
                )
            )
        view.set_viewport_position(viewport, False)

    def _point(self, row, column, old_line):
        line = self.view.line(self.view.text_point(row, 0))
        new_column = map_column(column, old_line, self.view.substr(line))
        return min(line.begin() + new_column, line.end())


# Show only the plugin's completions (the events) in the list `when` opens.
EVENT_LIST_ARGS = {
    "api_completions_only": True,
    "disable_auto_insert": True,
    "next_completion_if_showing": False,
}


def _open_event_list(view):
    if not view.is_auto_complete_visible():
        view.run_command("auto_complete", EVENT_LIST_ARGS)


class IruleListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        # on_modified fires for every edit (typing, Tab, Enter or a click in
        # the completion popup); command hooks miss some of those.
        if not is_irule(view) or len(view.sel()) != 1 or not view.sel()[0].empty():
            return
        point = view.sel()[0].b
        line_prefix = view.substr(sublime.Region(view.line(point).begin(), point))
        if should_open_event_list(line_prefix):
            # Run after the edit finishes: the popup `when` was picked from
            # has closed by then, and closing it cannot close this one.
            sublime.set_timeout(lambda: _open_event_list(view), 0)

    def on_pre_save(self, view):
        if is_irule(view) and sublime.load_settings(SETTINGS_FILE).get("format_on_save", False):
            view.run_command("irule_format", {"whole_file": True})

    def on_query_completions(self, view, prefix, locations):
        if not is_irule(view) or len(locations) != 1:
            return None
        point = locations[0]
        line = view.line(point)
        line_prefix = view.substr(sublime.Region(line.begin(), point))
        if not completing_event_name(line_prefix):
            return None
        rest_of_line = view.substr(sublime.Region(point, line.end()))
        items = []
        for name, details, deprecated in EVENTS:
            text, is_snippet = event_completion(name, rest_of_line)
            items.append(
                sublime.CompletionItem(
                    name,
                    annotation="deprecated" if deprecated else "event",
                    completion=text,
                    completion_format=(
                        sublime.COMPLETION_FORMAT_SNIPPET if is_snippet
                        else sublime.COMPLETION_FORMAT_TEXT
                    ),
                    kind=KIND_DEPRECATED_EVENT if deprecated else KIND_EVENT,
                    details=details,
                )
            )
        # Only events belong after `when`: hide command completions and buffer words.
        return sublime.CompletionList(
            items,
            flags=sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS,
        )

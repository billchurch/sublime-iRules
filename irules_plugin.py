"""Sublime Text commands and listeners for the iRules package."""

import re

import sublime
import sublime_plugin

from .irules_lib.context import completing_event_name
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
    """[(region, base_indent)] to format, merged so no two regions overlap."""
    selections = [region for region in view.sel() if not region.empty()]
    if whole_file or not selections:
        return [(sublime.Region(0, view.size()), "")]
    targets = []
    for region in selections:
        lines = view.line(region)
        if targets and targets[-1][0].end() >= lines.begin():
            targets[-1] = (targets[-1][0].cover(lines), targets[-1][1])
            continue
        base = LEADING_WHITESPACE_RE.match(view.substr(lines)).group(0)
        targets.append((lines, base))
    return targets


class FormatIruleCommand(sublime_plugin.TextCommand):
    """Re-indent the selected lines, or the whole file when nothing is selected."""

    def is_enabled(self, whole_file=False):
        return is_irule(self.view)

    def is_visible(self, whole_file=False):
        return is_irule(self.view)

    def run(self, edit, whole_file=False):
        view = self.view
        indent = indent_unit(view)
        carets = [view.rowcol(region.b) for region in view.sel()]
        viewport = view.viewport_position()
        # Replace from the end so earlier regions keep their offsets.
        for region, base in reversed(_format_targets(view, whole_file)):
            original = view.substr(region)
            formatted = format_irule(original, indent=indent, base_indent=base)
            if formatted != original:
                view.replace(edit, region, formatted)
        last_row = view.rowcol(view.size())[0]
        view.sel().clear()
        for row, col in carets:
            line = view.line(view.text_point(min(row, last_row), 0))
            view.sel().add(min(line.begin() + col, line.end()))
        view.set_viewport_position(viewport, False)


class IruleEditSettingsCommand(sublime_plugin.WindowCommand):
    """Open the package settings, whatever name the package is installed under."""

    def run(self):
        self.window.run_command(
            "edit_settings",
            {
                "base_file": "${packages}/%s/%s" % (__package__, SETTINGS_FILE),
                "default": "{\n\t$0\n}\n",
            },
        )


class IruleListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if is_irule(view) and sublime.load_settings(SETTINGS_FILE).get("format_on_save", False):
            view.run_command("format_irule", {"whole_file": True})

    def on_query_completions(self, view, prefix, locations):
        if not is_irule(view) or len(locations) != 1:
            return None
        point = locations[0]
        line_prefix = view.substr(sublime.Region(view.line(point).begin(), point))
        if not completing_event_name(line_prefix):
            return None
        items = [
            sublime.CompletionItem(
                name,
                annotation="deprecated" if deprecated else "event",
                kind=KIND_DEPRECATED_EVENT if deprecated else KIND_EVENT,
                details=details,
            )
            for name, details, deprecated in EVENTS
        ]
        # Only events belong after `when`: hide command completions and buffer words.
        return sublime.CompletionList(
            items,
            flags=sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS,
        )

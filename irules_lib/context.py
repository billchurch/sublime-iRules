"""Editor-context helpers that do not need Sublime Text."""

import re

_WHEN_PREFIX_RE = re.compile(r"^\s*when\s+[A-Za-z0-9_]*$")


def completing_event_name(line_prefix):
    """True when the text before the caret is `when` followed by a partial event name."""
    return _WHEN_PREFIX_RE.match(line_prefix) is not None


def _leading_whitespace(line):
    return len(line) - len(line.lstrip(" \t"))


def map_column(column, old_line, new_line):
    """Where a caret at column in old_line belongs after re-indenting to new_line.

    A caret in the text moves with the text; a caret inside the old
    indentation stays inside the new one.
    """
    old_indent = _leading_whitespace(old_line)
    new_indent = _leading_whitespace(new_line)
    if column >= old_indent:
        return column - old_indent + new_indent
    return min(column, new_indent)


EVENT_SNIPPET = "%s priority ${1:500} {\n\t$0\n}"


def event_completion(name, rest_of_line):
    """(text, is_snippet) to insert when completing an event after `when`.

    At the end of a line the event expands to a priority and a body, with
    500 selected first and the body next. If the line already continues
    after the caret (editing an existing handler), only the name is
    inserted so the rest of the line is not duplicated.
    """
    if rest_of_line.strip():
        return name, False
    return EVENT_SNIPPET % name, True


_WHEN_SPACE_RE = re.compile(r"^\s*when $")


def should_open_event_list(line_prefix):
    """True when the text before the caret is exactly `when ` on its line."""
    return _WHEN_SPACE_RE.match(line_prefix) is not None

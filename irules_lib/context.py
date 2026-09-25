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

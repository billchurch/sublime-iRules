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


# What to do after a text command, so `when` leads straight into the events.
SPACE_THEN_EVENT_LIST = "space_then_event_list"
OPEN_EVENT_LIST = "open_event_list"

_COMPLETION_COMMANDS = ("commit_completion", "insert_best_completion", "insert_completion")
_WHEN_WORD_RE = re.compile(r"^\s*when$")
_WHEN_SPACE_RE = re.compile(r"^\s*when $")


def after_text_command(command_name, args, line_prefix):
    """SPACE_THEN_EVENT_LIST, OPEN_EVENT_LIST or None.

    Completing `when` adds the space and opens the event list; typing the
    space after `when` opens it too.
    """
    if command_name in _COMPLETION_COMMANDS and _WHEN_WORD_RE.match(line_prefix):
        return SPACE_THEN_EVENT_LIST
    if (
        command_name == "insert"
        and (args or {}).get("characters") == " "
        and _WHEN_SPACE_RE.match(line_prefix)
    ):
        return OPEN_EVENT_LIST
    return None

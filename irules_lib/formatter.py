"""Re-indent iRule (Tcl) source.

Pure Python with no Sublime Text imports, so it can be unit-tested outside
the editor.

A small Tcl word scanner keeps a stack of open contexts across lines:

- ``QUOTE``: a double-quoted word. Text, except for ``[...]`` substitutions.
- ``BRACKET``: a ``[...]`` command substitution. A script.
- ``SCRIPT_BRACE``: a braced word whose ``{`` ends its line, such as a
  ``when`` or ``if`` body. A script.
- ``DATA_BRACE``: any other braced word, such as ``{<html>...}`` or a regex.
  Only nested braces matter inside it, as in Tcl.

Indentation is the number of open ``BRACKET`` and ``SCRIPT_BRACE`` contexts.
Lines that begin inside a ``QUOTE`` or ``DATA_BRACE`` are string content and
are never changed.
"""

QUOTE = '"'
BRACKET = "["
SCRIPT_BRACE = "{"
DATA_BRACE = "{data"

_INDENTING = (BRACKET, SCRIPT_BRACE)
_VERBATIM = (QUOTE, DATA_BRACE)
_WORD_START = " \t;["


def _ends_with_continuation(line):
    """True if the line ends with an odd number of backslashes."""
    count = len(line) - len(line.rstrip("\\"))
    return count % 2 == 1


def _depth(stack):
    return sum(1 for kind in stack if kind in _INDENTING)


def _in_verbatim(stack):
    return any(kind in _VERBATIM for kind in stack)


def _close_brace(stack):
    """Pop through the innermost brace. False if there is none to close."""
    if not any(kind in (SCRIPT_BRACE, DATA_BRACE) for kind in stack):
        return False
    while stack.pop() not in (SCRIPT_BRACE, DATA_BRACE):
        pass
    return True


def _opens_script(rest):
    """A brace starts a script body when nothing but a comment follows it."""
    rest = rest.strip()
    return rest == "" or rest.startswith("#")


def _scan(line, stack):
    """Advance the context stack over one line.

    Returns (leading, unmatched): leading counts the closing braces and
    brackets before any other character on the line; unmatched counts
    closers that had no open context to close.
    """
    leading = 0
    unmatched = 0
    at_start = True
    command_start = True
    i = 0
    while i < len(line):
        char = line[i]
        top = stack[-1] if stack else None
        if char == "\\":
            at_start = command_start = False
            i += 2
            continue
        if top == DATA_BRACE:
            if char == "{":
                stack.append(DATA_BRACE)
            elif char == "}":
                stack.pop()
            i += 1
            continue
        if top == QUOTE:
            if char == '"':
                stack.pop()
            elif char == "[":
                stack.append(BRACKET)
            i += 1
            continue
        # Script context: top level, a braced script body or [...].
        if char.isspace():
            i += 1
            continue
        if char == "#" and command_start:
            break  # comment to end of line
        if char in "}]":
            if char == "}":
                closed = _close_brace(stack)
            else:
                closed = top == BRACKET
                if closed:
                    stack.pop()
            if not closed:
                unmatched += 1
            if at_start:
                leading += 1
            command_start = False
            i += 1
            continue
        at_start = False
        if char == ";":
            command_start = True
        elif char == "[":
            stack.append(BRACKET)
            command_start = True
        elif char == "{":
            stack.append(SCRIPT_BRACE if _opens_script(line[i + 1:]) else DATA_BRACE)
            command_start = True
        elif char == '"' and (i == 0 or line[i - 1] in _WORD_START):
            stack.append(QUOTE)
            command_start = False
        else:
            command_start = False
        i += 1
    return leading, unmatched


def _indentation(level, first_level, indent, base_indent, outdent):
    if not outdent:
        return base_indent + indent * max(0, level)
    relative = level - first_level
    if relative >= 0:
        return base_indent + indent * relative
    return base_indent[: max(0, len(base_indent) - len(indent) * -relative)]


def format_irule(text, indent="    ", base_indent="", outdent=False):
    """Return text re-indented by nesting depth.

    indent is one level of indentation (e.g. four spaces or a tab).
    base_indent is prepended to every formatted line, which lets a caller
    format a selection that sits inside an already-indented block.
    outdent=True is for selections: the text may close blocks opened above
    it, so the first line keeps base_indent and lines that close further
    out are indented less than base_indent.
    String content (multi-line quoted words and braced words that start on
    the same line as their brace) is never changed.
    """
    rows = []  # (level, text); level None means emit text unchanged
    stack = []
    offset = 0
    continuing = False
    statement_depth = 0
    for raw in text.split("\n"):
        depth = _depth(stack) + offset
        if _in_verbatim(stack):
            rows.append((None, raw))
            _scan(raw, stack)
            continuing = _ends_with_continuation(raw)
            continue
        line = raw.strip()
        if not line:
            rows.append((None, ""))
            continuing = False
            continue
        leading, unmatched = _scan(line, stack)
        if _in_verbatim(stack):
            line = raw.lstrip()  # trailing spaces belong to the open string
        if continuing and leading == 0:
            level = max(depth, statement_depth + 1)
        else:
            level = depth - leading
        rows.append((level, line))
        if not continuing:
            statement_depth = depth
        if outdent:
            offset -= unmatched
        continuing = _ends_with_continuation(line) and not line.startswith("#")
    levels = [level for level, _ in rows if level is not None]
    first_level = levels[0] if levels else 0
    return "\n".join(
        line if level is None
        else _indentation(level, first_level, indent, base_indent, outdent) + line
        for level, line in rows
    )

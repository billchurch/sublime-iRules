"""Re-indent iRule (Tcl) source.

Pure Python with no Sublime Text imports, so it can be unit-tested outside
the editor. Indentation follows brace/bracket depth the way Tcl counts it:
unescaped braces are counted even inside double quotes and comments within a
braced body, because that is what the Tcl parser does.
"""

OPENERS = "{["
CLOSERS = "}]"
_WORD_START = " \t[;"


def _ends_with_continuation(line):
    """True if the line ends with an odd number of backslashes."""
    count = len(line) - len(line.rstrip("\\"))
    return count % 2 == 1


def _scan(line, depth, in_quote):
    """Scan one line.

    Returns (leading_closers, delta, in_quote) where leading_closers counts
    closing braces/brackets before any other character, delta is the net
    change in nesting depth and in_quote is whether a double-quoted word is
    still open at the end of the line.
    """
    is_comment = not in_quote and line.lstrip().startswith("#")
    if is_comment and depth == 0:
        # Top-level comments are ignored entirely by Tcl.
        return 0, 0, False
    leading = 0
    counting_leading = not in_quote
    delta = 0
    i = 0
    while i < len(line):
        char = line[i]
        if char == "\\":
            counting_leading = False
            i += 2
            continue
        if char == '"' and not is_comment:
            if in_quote:
                in_quote = False
            elif i == 0 or line[i - 1] in _WORD_START:
                in_quote = True
        elif char == "{" or (char == "[" and not is_comment):
            delta += 1
            counting_leading = False
        elif char == "}" or (char == "]" and not is_comment):
            delta -= 1
            if counting_leading:
                leading += 1
        elif not char.isspace():
            counting_leading = False
        i += 1
    return leading, delta, in_quote


def format_irule(text, indent="    ", base_indent=""):
    """Return text re-indented by nesting depth.

    indent is one level of indentation (e.g. four spaces or a tab).
    base_indent is prepended to every non-blank line, which lets a caller
    format a selection that sits inside an already-indented block.
    Lines inside a multi-line double-quoted string are left untouched.
    """
    out = []
    depth = 0
    in_quote = False
    continuing = False
    statement_depth = 0
    for raw in text.split("\n"):
        if in_quote:
            out.append(raw)
            _, delta, in_quote = _scan(raw, depth, True)
            depth = max(0, depth + delta)
            continuing = _ends_with_continuation(raw)
            continue
        line = raw.strip()
        if not line:
            out.append("")
            continuing = False
            continue
        leading, delta, in_quote = _scan(line, depth, False)
        if continuing and leading == 0:
            level = max(depth, statement_depth + 1)
        else:
            level = max(0, depth - leading)
        out.append(base_indent + indent * level + line)
        if not continuing:
            statement_depth = depth
        depth = max(0, depth + delta)
        continuing = _ends_with_continuation(line) and not line.startswith("#")
    return "\n".join(out)

"""Editor-context helpers that do not need Sublime Text."""

import re

_WHEN_PREFIX_RE = re.compile(r"^\s*when\s+[A-Za-z0-9_]*$")


def completing_event_name(line_prefix):
    """True when the text before the caret is `when` followed by a partial event name."""
    return _WHEN_PREFIX_RE.match(line_prefix) is not None

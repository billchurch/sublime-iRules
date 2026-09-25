"""Render generated package files from the merged database."""

import html
import json
import re
import xml.etree.ElementTree as ElementTree

from .build import DataError

GENERATED_SYNTAX_VARIABLES = (
    "most_likely_irule_code",
    "most_likely_irule_nscode",
    "most_likely_irule_events",
    "deprecated_irule_code",
    "deprecated_irule_events",
)
HAND_MAINTAINED_TCL_VARIABLES = (
    "most_likely_tcl_code",
    "most_likely_tcl_control_code",
    "disabled_tcl_code",
)
DETAILS_MAX = 160


def _variable_re(name):
    return re.compile(r"^(  %s: )'([^'\n]*)'$" % re.escape(name), re.M)


def tcl_names(syntax_text):
    """Names in the syntax's hand-maintained Tcl variables."""
    names = set()
    for variable in HAND_MAINTAINED_TCL_VARIABLES:
        match = _variable_re(variable).search(syntax_text)
        if match is None:
            raise DataError("syntax variable %r not found" % variable)
        names.update(match.group(2).split("|"))
    return names


def syntax_lists(database, skip):
    """Names for each generated syntax variable. skip: names the grammar handles itself."""
    commands, events = database["commands"], database["events"]
    return {
        "most_likely_irule_code": [
            n for n, i in commands.items()
            if "::" not in n and not i["deprecated"] and n not in skip
        ],
        "most_likely_irule_nscode": [
            n for n, i in commands.items() if "::" in n and not i["deprecated"]
        ],
        "most_likely_irule_events": [n for n, i in events.items() if not i["deprecated"]],
        "deprecated_irule_code": [
            n for n, i in commands.items() if i["deprecated"] and n not in skip
        ],
        "deprecated_irule_events": [n for n, i in events.items() if i["deprecated"]],
    }


def alternation(names):
    """Regex alternation, longest first so LSN::inbound-entry beats LSN::inbound."""
    return "|".join(sorted(set(names), key=lambda n: (-len(n), n)))


def _variable(syntax_text, name):
    match = _variable_re(name).search(syntax_text)
    return match.group(2).split("|") if match else []


def _check_prefix_conflicts(groups):
    """Raise if a name matched earlier would hide part of a name matched later.

    The grammar tries these alternations in order with \\b boundaries, so
    an earlier `LSN::inbound` would match the start of `LSN::inbound-entry`.
    Within one alternation, longest-first ordering already prevents this.
    """
    seen = set()
    for group in groups:
        for name in group:
            for index, char in enumerate(name):
                if index and not (char.isalnum() or char == "_") and name[:index] in seen:
                    raise DataError(
                        "syntax lists: %r is matched before %r and would hide it"
                        % (name[:index], name)
                    )
        seen.update(group)


def render_syntax(syntax_text, lists):
    # The order command-name and when-event try these alternations in.
    _check_prefix_conflicts([
        _variable(syntax_text, "most_likely_tcl_control_code"),
        lists["deprecated_irule_code"],
        _variable(syntax_text, "disabled_tcl_code"),
        _variable(syntax_text, "most_likely_tcl_code"),
        lists["most_likely_irule_code"],
        lists["most_likely_irule_nscode"],
    ])
    _check_prefix_conflicts([lists["deprecated_irule_events"], lists["most_likely_irule_events"]])
    for variable in GENERATED_SYNTAX_VARIABLES:
        if not lists[variable]:
            # An empty alternation would produce patterns like \b()\b that
            # match everywhere; it means the data or its parsing broke.
            raise DataError("syntax variable %r would be empty" % variable)
        replacement = alternation(lists[variable])
        syntax_text, count = _variable_re(variable).subn(
            lambda m: m.group(1) + "'" + replacement + "'", syntax_text
        )
        if count != 1:
            raise DataError(
                "syntax variable %r appears %d times in iRule.sublime-syntax, expected 1"
                % (variable, count)
            )
    return syntax_text


def details(info):
    """One-line HTML for a completion's details pane."""
    parts = []
    description = info["description"]
    if description:
        if len(description) > DETAILS_MAX:
            description = description[: DETAILS_MAX - 1].rstrip() + "…"
        parts.append(html.escape(description))
    if info["since"]:
        parts.append("BIG-IP %s+" % html.escape(info["since"]))
    if info["url"]:
        parts.append('<a href="%s">docs</a>' % html.escape(info["url"], quote=True))
    return " — ".join(parts)


def snippet_triggers(folder):
    """Tab triggers of the package's own .sublime-snippet files."""
    return {
        ElementTree.parse(str(path)).getroot().findtext("tabTrigger")
        for path in folder.glob("*.sublime-snippet")
    }


def render_completions(database, overrides, skip_triggers=frozenset()):
    """Command completions; skip_triggers are words a snippet already offers."""
    items = []
    for name, info in database["commands"].items():
        item = {"trigger": name, "kind": "function", "details": details(info)}
        if info["deprecated"]:
            item["kind"] = ["function", "d", "Deprecated"]
            item["annotation"] = "deprecated"
        else:
            item["annotation"] = name.split("::")[0] if "::" in name else "iRule"
        items.append(item)
    known = set(database["commands"])
    for name in overrides.get("tcl_completions", []):
        if name not in known:
            items.append({"trigger": name, "annotation": "Tcl", "kind": "keyword"})
    # A hand-written entry with the same trigger as a generated one replaces
    # its fields (e.g. adds snippet contents) but keeps the rest, such as the
    # docs details, so no trigger appears twice.
    by_trigger = {item["trigger"]: item for item in items}
    for extra in overrides.get("completions_extra", []):
        if extra["trigger"] in by_trigger:
            by_trigger[extra["trigger"]].update(extra)
        else:
            items.append(dict(extra))
            by_trigger[extra["trigger"]] = items[-1]
    items = [item for item in items if item["trigger"] not in skip_triggers]
    items.sort(key=lambda item: (item["trigger"].lower(), item["trigger"]))
    document = {"scope": "source.irule - comment - string", "completions": items}
    return json.dumps(document, indent=4, ensure_ascii=False) + "\n"


def render_events_module(database):
    lines = [
        '"""iRule events. Generated by `python3 -m tools.irules_data render`; do not edit."""',
        "",
        "# (name, details_html, deprecated)",
        "EVENTS = (",
    ]
    for name, info in database["events"].items():
        row = (name, details(info), info["deprecated"])
        lines.append("    %r," % (row,))
    lines.append(")")
    return "\n".join(lines) + "\n"

"""CLI: python3 -m tools.irules_data {fetch,render} [--check]"""

import argparse
import json
import sys
from pathlib import Path

from .build import DataError, build_database
from .fetch import scrape
from .render import (
    render_completions,
    render_events_module,
    render_syntax,
    syntax_lists,
    tcl_names,
)

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "clouddocs.json"
OVERRIDES = ROOT / "data" / "overrides.json"
SYNTAX = ROOT / "iRule.sublime-syntax"
COMPLETIONS = ROOT / "Completions" / "iRules-commands.sublime-completions"
EVENTS_MODULE = ROOT / "irules_lib" / "events.py"


def _read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write(path, text):
    with open(str(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _names(snapshot, kind):
    return {entry["name"] for entry in snapshot.get(kind, [])}


def cmd_fetch(check):
    snapshot = scrape()
    text = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    old_text = _read(SNAPSHOT)
    if not check:
        _write(SNAPSHOT, text)
        return 0
    if text == old_text:
        print("clouddocs snapshot is up to date")
        return 0
    old = json.loads(old_text) if old_text else {}
    for kind in ("commands", "events"):
        added = sorted(_names(snapshot, kind) - _names(old, kind))
        removed = sorted(_names(old, kind) - _names(snapshot, kind))
        if added:
            print("%s added upstream: %s" % (kind, ", ".join(added)))
        if removed:
            print("%s removed upstream: %s" % (kind, ", ".join(removed)))
    print("clouddocs changed; run `python3 -m tools.irules_data fetch` then `render`")
    return 1


def generated_outputs():
    snapshot = json.loads(_read(SNAPSHOT))
    overrides = json.loads(_read(OVERRIDES))
    database = build_database(snapshot, overrides)
    syntax_text = _read(SYNTAX)
    skip = set(overrides.get("syntax_skip", [])) | tcl_names(syntax_text)
    return {
        SYNTAX: render_syntax(syntax_text, syntax_lists(database, skip)),
        COMPLETIONS: render_completions(database, overrides),
        EVENTS_MODULE: render_events_module(database),
    }


def cmd_render(check):
    try:
        outputs = generated_outputs()
    except DataError as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    stale = [path for path, text in outputs.items() if _read(path) != text]
    for path in stale:
        if check:
            print("out of date: %s" % path.relative_to(ROOT))
        else:
            _write(path, outputs[path])
            print("wrote %s" % path.relative_to(ROOT))
    return 1 if (check and stale) else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m tools.irules_data")
    parser.add_argument("command", choices=("fetch", "render"))
    parser.add_argument("--check", action="store_true", help="report differences, write nothing")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        return cmd_fetch(args.check)
    return cmd_render(args.check)


if __name__ == "__main__":
    sys.exit(main())

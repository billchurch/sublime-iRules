"""Merge a clouddocs snapshot with the hand-maintained overrides."""

import re

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z0-9_][A-Za-z0-9_-]*)*$")


class DataError(ValueError):
    pass


def _info(description="", url=None, deprecated=False, since=None):
    return {"description": description, "url": url, "deprecated": deprecated, "since": since}


def build_database(snapshot, overrides):
    """Return {"commands": {name: info}, "events": {name: info}}.

    info is {"description", "url", "deprecated", "since"}. Raises DataError
    when the overrides are inconsistent with the snapshot, so stale
    overrides surface instead of silently piling up.
    """
    database = {}
    for kind in ("commands", "events"):
        kind_overrides = overrides.get(kind, {})
        rename = kind_overrides.get("rename", {})
        exclude = set(kind_overrides.get("exclude", []))
        merged = {}
        rejected = []
        for entry in snapshot[kind]:
            if entry["name"] in exclude:
                continue
            name = rename.get(entry["name"], entry["name"])
            if not NAME_RE.match(name):
                rejected.append(entry["name"])
                continue
            merged[name] = _info(
                entry["description"],
                entry["url"],
                entry["deprecated"],
                snapshot["introduced"].get(entry["name"]),
            )
        if rejected:
            raise DataError(
                "%s: names not valid as iRule identifiers, add them to %s.exclude "
                "or %s.rename in data/overrides.json: %s"
                % (kind, kind, kind, ", ".join(sorted(rejected)))
            )
        for name, extra in kind_overrides.get("add", {}).items():
            if name in merged:
                raise DataError(
                    "%s.add: %s is now documented upstream; delete it from data/overrides.json"
                    % (kind, name)
                )
            if not NAME_RE.match(name):
                raise DataError("%s.add: %r is not a valid iRule identifier" % (kind, name))
            merged[name] = _info(
                extra.get("description", ""),
                extra.get("url"),
                extra.get("deprecated", False),
                extra.get("since"),
            )
        for name in kind_overrides.get("deprecate", []):
            if name not in merged:
                raise DataError("%s.deprecate: unknown name %s" % (kind, name))
            merged[name]["deprecated"] = True
        database[kind] = dict(sorted(merged.items()))
    return database

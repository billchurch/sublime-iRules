"""Shared fixtures for the tools.irules_data tests."""


def snapshot(commands=(), events=(), introduced=None):
    def entry(name, deprecated=False):
        return {"name": name, "description": name.lower(), "url": "u/" + name, "deprecated": deprecated}
    return {
        "commands": [entry(*c) if isinstance(c, tuple) else entry(c) for c in commands],
        "events": [entry(*e) if isinstance(e, tuple) else entry(e) for e in events],
        "introduced": introduced or {},
    }

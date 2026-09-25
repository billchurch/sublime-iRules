"""Download the clouddocs pages and build a raw snapshot."""

import time
import urllib.request

from .parse import (
    BASE_URL,
    parse_master_list,
    parse_version_index,
    parse_version_page,
)

USER_AGENT = "sublime-iRules data generator (+https://github.com/billchurch/sublime-iRules)"


def fetch_page(name, retries=3):
    request = urllib.request.Request(BASE_URL + name, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def scrape(fetch=fetch_page):
    """Return the snapshot dict written to data/clouddocs.json.

    The snapshot holds no timestamps, so re-scraping unchanged docs yields
    byte-identical output and `fetch --check` stays quiet.
    """
    introduced = {}
    for version, filename in parse_version_index(fetch("BIGIP_Commands_by_Version.html")):
        changes = parse_version_page(fetch(filename))
        for name in changes["commands"] + changes["events"]:
            introduced.setdefault(name, version)
    return {
        "source": BASE_URL,
        "commands": sorted(parse_master_list(fetch("Commands.html")), key=lambda e: e["name"]),
        "events": sorted(parse_master_list(fetch("Events.html")), key=lambda e: e["name"]),
        "introduced": dict(sorted(introduced.items())),
    }

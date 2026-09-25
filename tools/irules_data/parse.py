"""Parse the clouddocs.f5.com iRules reference (Sphinx-generated HTML)."""

import html
import re

BASE_URL = "https://clouddocs.f5.com/api/irules/"

_SECTION_RE = re.compile(r'<div class="section" id="([^"]+)">')
# Link text may carry inline markup such as <code>; _clean strips it. Only
# links to other pages count: in-page anchors ("#...") are table-of-contents.
# Some hrefs lack ".html" (UDP__max_buf_pkts), so do not require it.
_ITEM_RE = re.compile(
    r'<li><a class="reference (?:external|internal)" href="([^"#][^"]*)">(.*?)</a>(.*?)</li>',
    re.S,
)
_TAG_RE = re.compile(r"<[^>]+>")
_VERSION_RE = re.compile(r"BIGIP_LTM_v(\d+(?:_\d+)*)\.html")


def _clean(text):
    text = html.unescape(_TAG_RE.sub("", text))
    return " ".join(text.split()).lstrip("- ").strip()


def _sections(page):
    """Yield (section_id, html) for each Sphinx section inside the article."""
    end_of_article = page.find("</article>")
    if end_of_article != -1:
        page = page[:end_of_article]
    matches = list(_SECTION_RE.finditer(page))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(page)
        yield match.group(1), page[match.end():end]


def parse_master_list(page):
    """Entries from Commands.html or Events.html, first occurrence wins.

    Each entry is {"name", "description", "url", "deprecated"}. An entry is
    deprecated when its section id ends in "-deprecated" (for example
    "NAME (Deprecated)") or its description starts with "Deprecated".
    """
    entries = {}
    for section_id, body in _sections(page):
        section_deprecated = section_id.endswith("-deprecated")
        for href, name, rest in _ITEM_RE.findall(body):
            name = _clean(name)
            if name in entries:
                continue
            description = _clean(rest)
            entries[name] = {
                "name": name,
                "description": description,
                "url": BASE_URL + href,
                "deprecated": section_deprecated
                or description.lower().startswith("deprecated"),
            }
    return list(entries.values())


def parse_version_index(page):
    """[(version, filename)] from BIGIP_Commands_by_Version.html, oldest first."""
    seen = {}
    for match in _VERSION_RE.finditer(page):
        seen.setdefault(match.group(0), match.group(1).replace("_", "."))
    return [(version, filename) for filename, version in seen.items()]


def parse_version_page(page):
    """Names introduced on one BIGIP_LTM_v*.html page: {"commands": [], "events": []}."""
    found = {"commands": [], "events": []}
    for section_id, body in _sections(page):
        for kind in found:
            if section_id.startswith(kind + "-introduced-in-"):
                found[kind].extend(_clean(name) for _, name, _ in _ITEM_RE.findall(body))
    return found

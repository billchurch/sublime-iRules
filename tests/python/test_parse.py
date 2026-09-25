import unittest

from tools.irules_data.parse import (
    parse_master_list,
    parse_version_index,
    parse_version_page,
)

MASTER = """
<nav><ul><li><a class="reference external" href="../index.html">Site nav</a></li></ul></nav>
<article>
<div class="section" id="http">
<h2>HTTP</h2>
<ul class="simple">
<li><a class="reference external" href="HTTP__uri.html">HTTP::uri</a> - Returns or sets
the <strong>URI</strong> &amp; path.</li>
<li><a class="reference external" href="local_addr.html">local_addr</a> - Deprecated: Use IP::local_addr instead</li>
<li><a class="reference external" href="HTTP__uri.html">HTTP::uri</a> - duplicate listing</li>
</ul>
</div>
<div class="section" id="name-deprecated">
<h2>NAME (Deprecated)</h2>
<ul class="simple">
<li><a class="reference external" href="NAME__lookup.html">NAME::lookup</a> - Performs DNS query</li>
</ul>
</div>
</article>
<footer><ul><li><a class="reference external" href="x.html">Footer</a></li></ul></footer>
"""

VERSION_INDEX = """
<li><a class="reference external" href="BIGIP_LTM_v9_0_0.html">BIG-IP LTM v9.0.0</a></li>
<li><a class="reference external" href="BIGIP_LTM_v21_0_0.html">BIG-IP LTM v21.0.0</a></li>
<li><a class="reference external" href="BIGIP_LTM_v21_0_0.html">again</a></li>
"""

VERSION_PAGE = """
<article>
<div class="section" id="commands-introduced-in-big-ip-ltm-21-0-0">
<ul><li><a class="reference external" href="JSON__parse.html">JSON::parse</a> - parses JSON</li></ul>
</div>
<div class="section" id="commands-updated-in-big-ip-ltm-21-0-0">
<ul><li><a class="reference external" href="HTTP__uri.html">HTTP::uri</a> - updated</li></ul>
</div>
<div class="section" id="events-introduced-in-big-ip-ltm-21-0-0">
<ul><li><a class="reference external" href="JSON_REQUEST.html">JSON_REQUEST</a> - triggered</li></ul>
</div>
</article>
"""


class ParseTests(unittest.TestCase):
    def test_master_list_reads_names_descriptions_and_deprecation(self):
        entries = {e["name"]: e for e in parse_master_list(MASTER)}
        self.assertEqual(sorted(entries), ["HTTP::uri", "NAME::lookup", "local_addr"])
        self.assertEqual(entries["HTTP::uri"]["description"], "Returns or sets the URI & path.")
        self.assertEqual(entries["HTTP::uri"]["url"], "https://clouddocs.f5.com/api/irules/HTTP__uri.html")
        self.assertFalse(entries["HTTP::uri"]["deprecated"])
        self.assertTrue(entries["local_addr"]["deprecated"])
        self.assertTrue(entries["NAME::lookup"]["deprecated"])

    def test_version_index_is_deduplicated_and_ordered(self):
        self.assertEqual(
            parse_version_index(VERSION_INDEX),
            [("9.0.0", "BIGIP_LTM_v9_0_0.html"), ("21.0.0", "BIGIP_LTM_v21_0_0.html")],
        )

    def test_version_page_only_reads_introduced_sections(self):
        self.assertEqual(
            parse_version_page(VERSION_PAGE),
            {"commands": ["JSON::parse"], "events": ["JSON_REQUEST"]},
        )



if __name__ == "__main__":
    unittest.main()


class MarkupToleranceTests(unittest.TestCase):
    def test_link_text_with_inner_markup_is_not_dropped(self):
        page = (
            '<article><div class="section" id="http"><ul>'
            '<li><a class="reference external" href="HTTP__foo.html"><code>HTTP::foo</code></a> - foo</li>'
            '<li><a class="reference internal" href="HTTP__bar.html">HTTP::bar</a> - bar</li>'
            '<li><a class="reference internal" href="#anchor">Not a page</a></li>'
            "</ul></div></article>"
        )
        self.assertEqual(sorted(e["name"] for e in parse_master_list(page)), ["HTTP::bar", "HTTP::foo"])

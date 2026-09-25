import io
import unittest
import urllib.error
from contextlib import redirect_stderr
from unittest import mock

from tools.irules_data import __main__ as cli
from tools.irules_data.fetch import scrape


class FetchNetworkErrorTests(unittest.TestCase):
    def test_network_failure_is_reported_distinctly_from_docs_drift(self):
        failing = mock.Mock(side_effect=urllib.error.URLError("timed out"))
        stderr = io.StringIO()
        with mock.patch.object(cli, "scrape", failing), redirect_stderr(stderr):
            self.assertEqual(cli.cmd_fetch(check=True), 3)
        self.assertIn("network", stderr.getvalue())


class IntroducedVersionTests(unittest.TestCase):
    def test_earliest_version_wins_whatever_the_index_order(self):
        pages = {
            "BIGIP_Commands_by_Version.html": (
                '<a href="BIGIP_LTM_v21_0_0.html">21</a><a href="BIGIP_LTM_v9_10_0.html">9.10</a>'
                '<a href="BIGIP_LTM_v9_2_0.html">9.2</a>'
            ),
            "Commands.html": "<article></article>",
            "Events.html": "<article></article>",
        }
        introduced = (
            '<article><div class="section" id="commands-introduced-in-x"><ul>'
            '<li><a class="reference external" href="X.html">X::y</a> - x</li></ul></div></article>'
        )
        for name in ("BIGIP_LTM_v21_0_0.html", "BIGIP_LTM_v9_10_0.html", "BIGIP_LTM_v9_2_0.html"):
            pages[name] = introduced
        self.assertEqual(scrape(fetch=pages.__getitem__)["introduced"], {"X::y": "9.2.0"})


if __name__ == "__main__":
    unittest.main()

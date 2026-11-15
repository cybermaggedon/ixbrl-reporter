"""
Unit tests for ixbrl_reporter.view (the 'view' output)
"""
import os
import re
import tempfile
import threading
import urllib.error
import urllib.request
from io import StringIO

from ixbrl_reporter.view import serve, ACCOUNTS, LAUNCHER


def view_folders():
    root = tempfile.gettempdir()
    return {d for d in os.listdir(root) if d.startswith("ixbrl-reporter-view-")}


class FakeStdout(StringIO):
    def __init__(self, tty):
        super().__init__()
        self.tty = tty

    def isatty(self):
        return self.tty


def run_serve(content, checks, **kw):
    """Run serve() with a fake browser; checks(url) runs, then Ctrl-C."""
    out = StringIO()

    def fake_open(url):
        def work():
            try:
                checks(url)
            finally:
                os.kill(os.getpid(), 2)  # Ctrl-C

        threading.Thread(target=work).start()

    serve(content, open_browser=fake_open, out=out, **kw)
    return out.getvalue()


class TestView:
    def test_serves_accounts_and_launcher_on_loopback_then_cleans_up(self, monkeypatch):
        monkeypatch.delenv("GRAFFITI_PROXY", raising=False)
        before = view_folders()
        got = {}

        def checks(url):
            base = url.split("/open-in-graffiti")[0]
            got["url"] = url
            got["accounts"] = urllib.request.urlopen(base + "/" + ACCOUNTS).read()
            got["launcher"] = urllib.request.urlopen(base + "/" + LAUNCHER).read()
            try:
                urllib.request.urlopen(base + "/nothing-here")
            except urllib.error.HTTPError as e:
                got["missing"] = e.code
            req = urllib.request.Request(base + "/" + ACCOUNTS, headers={"Host": "evil.example"})
            try:
                urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                got["badhost"] = e.code
            got["during"] = view_folders() - before

        out = run_serve("<html>accounts</html>", checks)
        assert re.match(r"http://127\.0\.0\.1:\d+/open-in-graffiti\.html\?file=accounts\.html$", got["url"])
        assert got["accounts"] == b"<html>accounts</html>"
        assert b"Open in Graffiti" in got["launcher"]
        assert got["missing"] == 404
        assert got["badhost"] == 403
        assert "127.0.0.1 only" in out
        assert len(got["during"]) == 1, "folder should exist while serving"
        assert view_folders() == before, "folder should be gone after Ctrl-C"

    def test_proxy_override_goes_in_the_url(self):
        got = {}
        run_serve("x", lambda url: got.update(url=url), proxy="http://localhost:3999")
        assert got["url"].endswith("&proxy=http%3A%2F%2Flocalhost%3A3999")

    def test_proxy_from_environment(self, monkeypatch):
        monkeypatch.setenv("GRAFFITI_PROXY", "http://localhost:3998")
        got = {}
        run_serve("x", lambda url: got.update(url=url))
        assert "proxy=http%3A%2F%2Flocalhost%3A3998" in got["url"]

    def test_redirected_stdout_gets_the_ixbrl_before_serving(self):
        save, seen = FakeStdout(tty=False), {}
        run_serve("<html>accounts</html>", lambda url: seen.update(file=save.getvalue()), save=save)
        assert seen["file"] == "<html>accounts</html>"

    def test_terminal_stdout_gets_nothing(self):
        save = FakeStdout(tty=True)
        run_serve("<html>accounts</html>", lambda url: None, save=save)
        assert save.getvalue() == ""

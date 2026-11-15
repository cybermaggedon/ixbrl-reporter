"""
The 'view' output: serve the generated iXBRL from a temporary folder on
127.0.0.1 and open a launcher page that hands it to Graffiti in the browser.
When stdout is redirected the same iXBRL is also written there first.
Standard library only.  The file is not uploaded: the launcher page passes
it to the Graffiti tab with postMessage (the way the Graffiti bookmarklet
does).  Set GRAFFITI_PROXY to use a Graffiti server other than
https://ai.stechanalytics.com.
"""
import functools
import http.server
import os
import shutil
import signal
import sys
import tempfile
import urllib.parse
import webbrowser

DEFAULT_PROXY = "https://ai.stechanalytics.com"
ACCOUNTS = "accounts.html"
LAUNCHER = "open-in-graffiti.html"

LAUNCHER_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Open in Graffiti</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 16px/1.5 sans-serif; margin: 2rem auto; max-width: 36rem; padding: 0 1rem; }
  button { font: inherit; padding: .5rem 1rem; }
  #note { margin-top: 1rem; }
</style>
</head>
<body>
<h1>Open these accounts in Graffiti</h1>
<p>Graffiti shows the tags, checks and ratios in your accounts. Your file goes from this page to the Graffiti tab inside your browser. It is not uploaded.</p>
<p><button id="open" type="button">Open in Graffiti</button></p>
<p id="note" role="status"></p>
<script>
// Opens <proxy>/view?open=1, waits for its 'graffiti-open-ready', then posts the file with this page's own
// address. ?file=<name> picks the accounts beside this page; ?proxy=<url> picks the Graffiti server.
(function() {
  var params = new URLSearchParams(location.search);
  var file = params.get('file') || 'accounts.html';
  var proxy = (params.get('proxy') || 'https://ai.stechanalytics.com').replace(/\\/$/, '');
  var note = document.getElementById('note');
  document.getElementById('open').addEventListener('click', function() {
    // Opened in the click itself, or the browser blocks it as a pop-up.
    var tab = window.open(proxy + '/view?open=1', '_blank');
    if(!tab) { note.textContent = 'Your browser blocked the Graffiti tab. Allow pop-ups for this page and press the button again.'; return; }
    note.textContent = 'Opening Graffiti...';
    var sourceUrl = new URL(file, location.href).href;
    var request = fetch(sourceUrl).then(function(response) {
      if(!response.ok) throw new Error('HTTP ' + response.status);
      return response.arrayBuffer();
    });
    window.addEventListener('message', function onReady(event) {
      if(event.source !== tab || !event.data || event.data.type !== 'graffiti-open-ready') return;
      window.removeEventListener('message', onReady);
      request.then(function(bytes) {
        var xml = /^\\s*<\\?xml/.test(new TextDecoder().decode(bytes.slice(0, 64)));
        var name = sourceUrl.split('/').pop().split('?')[0] || 'accounts.html';
        tab.postMessage({
          type: 'graffiti-open',
          file: new File([bytes], name, { type: xml ? 'application/xhtml+xml' : 'text/html' }),
          sourceUrl: sourceUrl
        }, event.origin);
        note.textContent = 'Sent to Graffiti. You can close this tab.';
      }).catch(function(error) {
        tab.close();
        note.textContent = 'Could not read ' + file + ' (' + error.message + ').';
      });
    });
  });
})();
</script>
</body>
</html>
"""


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Static files from one folder; refuses any Host other than loopback."""

    def do_GET(self):
        if self.headers.get("Host", "").rsplit(":", 1)[0] not in (
            "127.0.0.1", "localhost"
        ):
            self.send_error(403)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


def serve(content, proxy=None, open_browser=webbrowser.open, out=sys.stderr,
          save=None):
    """Serve content (the iXBRL text) until Ctrl-C, then remove the folder.

    When save (default sys.stdout) is not a terminal, the content is also
    written to it and flushed before serving, so
    'report view > accounts.html' keeps the file."""
    save = sys.stdout if save is None else save
    if not save.isatty():
        save.write(content)
        save.flush()
    proxy = proxy or os.environ.get("GRAFFITI_PROXY") or DEFAULT_PROXY
    folder = tempfile.mkdtemp(prefix="ixbrl-reporter-view-")
    try:
        with open(os.path.join(folder, ACCOUNTS), "w", encoding="utf-8") as f:
            f.write(content)
        with open(os.path.join(folder, LAUNCHER), "w", encoding="utf-8") as f:
            f.write(LAUNCHER_HTML)
        handler = functools.partial(_Handler, directory=folder)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        url = "http://127.0.0.1:%d/%s?file=%s" % (
            server.server_port, LAUNCHER, ACCOUNTS
        )
        if proxy != DEFAULT_PROXY:
            url += "&proxy=" + urllib.parse.quote(proxy, safe="")
        out.write("Serving %s on 127.0.0.1 only.  Press Ctrl-C to stop.\n" % url)
        # SIGTERM stops it the same way as Ctrl-C.
        signal.signal(signal.SIGTERM, signal.default_int_handler)
        try:
            open_browser(url)
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        shutil.rmtree(folder, ignore_errors=True)

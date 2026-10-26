"""HTTP 308 redirects are followed on every supported Python (3.10's
urllib does not by itself: anthropic.com moved articles with a 308)."""
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from extractor import utils


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/old":
            self.send_response(308)
            self.send_header("Location", "/new")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"moved here")

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_permanent_redirect_is_followed(server, monkeypatch):
    monkeypatch.setattr(urllib.request, "_opener", None)
    utils.follow_permanent_redirects()
    with urllib.request.urlopen(server + "/old", timeout=5) as response:
        assert response.read() == b"moved here"
        assert response.url.endswith("/new")

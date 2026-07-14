"""Pytest fixtures for the PotionCode.io browser tests.

The site is plain static files, so we serve the repo root with Python's
stdlib ``http.server`` (the same thing as ``python -m http.server``, just on
an ephemeral port picked per test session) and hand the tests its base URL.
No dev dependency beyond Playwright itself.
"""
import functools
import http.server
import socketserver
import threading
from pathlib import Path

import pytest

# Repo root = the folder above tests/, regardless of where pytest is run from.
ROOT = Path(__file__).resolve().parent.parent


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that doesn't spam the test output."""

    def log_message(self, *args):  # noqa: D401 - silence per-request logging
        pass


@pytest.fixture(scope="session")
def live_server():
    """Serve the repo root and yield its base URL, e.g. http://127.0.0.1:54321."""
    handler = functools.partial(_QuietHandler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()

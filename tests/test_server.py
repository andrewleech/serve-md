"""Tests for server behaviour: handler routing and port fallback."""

from __future__ import annotations

import socket
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from serve_md.server import make_handler


def _run(server: HTTPServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def test_handler_serves_rendered_page_and_mtime(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# Hi\n", encoding="utf-8")

    server = HTTPServer(("127.0.0.1", 0), make_handler(md))
    _run(server)
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"{base}/") as resp:
            assert "Hi" in resp.read().decode()
        with urllib.request.urlopen(f"{base}/__mtime") as resp:
            assert "mtime" in resp.read().decode()
    finally:
        server.shutdown()
        server.server_close()


def test_handler_blocks_path_traversal(tmp_path: Path) -> None:
    (tmp_path / "secret").mkdir()
    secret = tmp_path / "secret" / "creds.txt"
    secret.write_text("nope", encoding="utf-8")
    served = tmp_path / "secret" / "doc.md"
    served.write_text("# served\n", encoding="utf-8")

    server = HTTPServer(("127.0.0.1", 0), make_handler(served))
    _run(server)
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            urllib.request.urlopen(f"{base}/../creds.txt")
            raised = None
        except urllib.error.HTTPError as exc:
            raised = exc.code
        assert raised in (403, 404)
    finally:
        server.shutdown()
        server.server_close()


def test_port_in_use_is_detectable() -> None:
    # Documents the precondition serve() relies on: binding a taken port raises.
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    taken = blocker.getsockname()[1]
    try:
        raised = False
        try:
            HTTPServer(("127.0.0.1", taken), make_handler(Path("x.md"))).server_close()
        except OSError:
            raised = True
        assert raised
    finally:
        blocker.close()

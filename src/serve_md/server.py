"""Live-reloading HTTP server for a single Markdown or HTML file."""

from __future__ import annotations

import http.server
import json
import mimetypes
import shutil
import subprocess
from pathlib import Path

from .render import render

PORT_SCAN_RANGE = 100

# Default location of the Tailscale CLI installed by the Windows installer,
# reachable from WSL via the /mnt/c mount when it is not on PATH.
_WSL_TAILSCALE = Path("/mnt/c/Program Files/Tailscale/tailscale.exe")


def _find_tailscale() -> str | None:
    """Locate a usable Tailscale CLI.

    Prefers a native ``tailscale`` on PATH, then ``tailscale.exe`` on PATH (WSL),
    and finally the Windows installer's default path. Returns ``None`` if none is
    found.
    """
    for name in ("tailscale", "tailscale.exe"):
        found = shutil.which(name)
        if found is not None:
            return found
    if _WSL_TAILSCALE.exists():
        return str(_WSL_TAILSCALE)
    return None


def _detect_hostname() -> str:
    """Return the Tailscale DNS name if available, else ``localhost``."""
    tailscale = _find_tailscale()
    if tailscale is None:
        return "localhost"
    try:
        out = subprocess.check_output([tailscale, "status", "--json"], timeout=2)
        name = json.loads(out)["Self"]["DNSName"].rstrip(".")
        return str(name)
    except Exception:
        return "localhost"


def make_handler(file_path: Path) -> type[http.server.BaseHTTPRequestHandler]:
    """Build a request handler that serves ``file_path`` and its sibling assets."""
    root = file_path.parent

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0].split("#", 1)[0]
            if path == "/__mtime":
                self._send_mtime()
                return
            if path in ("/", "/" + file_path.name):
                self._send_page()
                return
            self._send_asset(path)

        def _send_page(self) -> None:
            body = render(file_path).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def _send_mtime(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"mtime": file_path.stat().st_mtime}).encode())

        def _send_asset(self, path: str) -> None:
            # Static sibling asset, confined to the served file's directory.
            try:
                target = (root / path.lstrip("/")).resolve()
                target.relative_to(root)  # block path traversal
            except (ValueError, OSError):
                self.send_error(403)
                return
            if not target.is_file():
                self.send_error(404)
                return
            ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(target.read_bytes())

        def log_message(self, fmt: str, *args: object) -> None:
            pass  # silence the default per-request logging

    return Handler


def serve(
    file_path: Path,
    *,
    host: str,
    port: int,
    open_browser: bool = False,
) -> None:
    """Serve ``file_path`` with live reload until interrupted.

    Binds to ``port`` and, if it is already in use, scans the next
    ``PORT_SCAN_RANGE`` ports for a free one.
    """
    handler_cls = make_handler(file_path)

    server: http.server.HTTPServer | None = None
    last_error: OSError | None = None
    for candidate in range(port, port + PORT_SCAN_RANGE):
        try:
            server = http.server.HTTPServer((host, candidate), handler_cls)
            break
        except OSError as exc:
            last_error = exc
    if server is None:
        msg = f"no free port in range {port}-{port + PORT_SCAN_RANGE - 1}"
        raise SystemExit(msg) from last_error

    bound_port = server.server_address[1]
    url = f"http://{_detect_hostname()}:{bound_port}"
    # flush so the URL is visible immediately even when stdout is redirected.
    print(f"Serving {file_path.name} at {url} (live reload)", flush=True)

    if open_browser:
        import threading
        import webbrowser

        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()

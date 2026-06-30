"""Command-line entry point for serve-md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .server import serve

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 57642


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="serve-md",
        description=(
            "Render a Markdown file as styled HTML, or serve an HTML file directly, "
            "with live reload. Sibling files in the same directory are served as "
            "static assets so relative references resolve."
        ),
    )
    parser.add_argument("file", type=Path, help="path to a .md or .html file")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=(f"port to serve on (default: {DEFAULT_PORT}); if taken, the next free port is used"),
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"address to bind (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="open the page in a browser window on start (off by default)",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    file_path: Path = args.file.resolve()
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1
    if not file_path.is_file():
        print(f"Not a file: {file_path}", file=sys.stderr)
        return 1

    serve(
        file_path,
        host=args.host,
        port=args.port,
        open_browser=args.browser,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

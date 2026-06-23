# serve-md — project notes for Claude

A small CLI that serves a single Markdown or HTML file as a live-reloading local
web page. Installed as a `uv` tool; the console entry point is
`serve_md.cli:main`.

## Layout

- `src/serve_md/render.py` — pure functions turning a file into an HTML string
  (`render_markdown`, `render_html`, `render`, `is_html`) plus the `CSS` and
  `RELOAD_JS` constants. No I/O beyond reading the source file. Keep this
  side-effect free so it stays trivially testable.
- `src/serve_md/server.py` — the HTTP layer: `make_handler` builds the request
  handler (routes `/`, `/__mtime`, and confined static sibling assets), and
  `serve` binds a port (scanning upward on conflict) and runs the loop.
- `src/serve_md/cli.py` — argparse front end and `main`.
- `tests/` — pytest; `test_render.py` covers rendering, `test_server.py` drives
  a real `HTTPServer` on an ephemeral port.

## Conventions

- Python ≥ 3.10, `from __future__ import annotations` in every module.
- mypy runs in `strict` mode and ruff lint must pass; both are wired into
  pre-commit. Run `uv run mypy` and `uv run ruff check .` before committing.
- The live-reload mechanism is mtime polling: the page fetches `/__mtime` every
  500 ms and reloads when it changes. Both the Markdown and raw-HTML paths embed
  the same `RELOAD_JS`.
- Static asset serving is deliberately confined to the served file's parent
  directory via a `relative_to` check — preserve that guard when editing
  `make_handler`.

## Common commands

```bash
uv sync                 # dev environment
uv run pytest           # tests
uv run ruff check .     # lint
uv run mypy             # type-check
uv tool install . --reinstall   # install/update the local tool
```

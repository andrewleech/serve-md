# serve-md

Render a Markdown file as styled HTML — or serve an HTML file directly — on a
local web server that auto-refreshes the browser whenever the file changes.

- `.md` files are rendered to a dark-themed, self-contained HTML page
  (tables, fenced code with syntax highlighting, table of contents, smart quotes).
- `.html` files are served as-is, with a live-reload snippet injected.
- Sibling files in the same directory (css, js, images, ...) are served as
  static assets, so relative references in an HTML page resolve. Access is
  confined to the served file's directory.
- The browser reloads automatically when the file changes, preserving scroll
  position.

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv tool install .
```

Run it from anywhere afterwards:

```bash
serve-md README.md
```

To update after pulling changes, re-run `uv tool install .` (or
`uv tool install . --reinstall`). Remove it with `uv tool uninstall serve-md`.

### Run without installing

```bash
uv run serve-md README.md
```

## Usage

```text
serve-md [-p PORT] [--host HOST] [--no-browser] file

  file                  path to a .md or .html file
  -p, --port PORT       port to serve on (default: 57642); if taken, the next
                        free port is used
  --host HOST           address to bind (default: 0.0.0.0)
  --no-browser          do not open a browser window
  -V, --version         show version and exit
```

If the default port is in use, `serve-md` scans the next 100 ports and binds to
the first free one, printing the URL it actually chose. When a Tailscale node is
detected, the printed URL uses its DNS name so the page is reachable from other
devices on the tailnet.

## Development

```bash
uv sync                 # create .venv with dev dependencies
uv run pytest           # run tests
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy             # type-check
```

Install the git hooks so the same checks run on commit:

```bash
uv run pre-commit install
```

## License

[MIT](LICENSE)

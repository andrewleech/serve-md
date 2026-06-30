# serve-md

Render a Markdown file as styled HTML — or serve an HTML file directly — on a
local web server that auto-refreshes the browser whenever the file changes.

- `.md` files are rendered to a self-contained HTML page (tables, fenced code
  with syntax highlighting, table of contents, smart quotes), with a top-right
  toggle to switch between dark and light themes. It defaults to your OS
  preference and remembers your choice.
- `.html` files are served as-is, with a live-reload snippet injected.
- Sibling files in the same directory (css, js, images, ...) are served as
  static assets, so relative references in an HTML page resolve. Access is
  confined to the served file's directory.
- The browser reloads automatically when the file changes, preserving scroll
  position.

## Install

Requires [uv](https://docs.astral.sh/uv/). Install straight from GitHub:

```bash
uv tool install git+https://github.com/andrewleech/serve-md
```

Run it from anywhere afterwards:

```bash
serve-md README.md
```

Pin to a tag, branch, or commit by appending `@<ref>`:

```bash
uv tool install git+https://github.com/andrewleech/serve-md@v0.1.0
```

Update with `uv tool upgrade serve-md` (or re-run the install with
`--reinstall`). Remove it with `uv tool uninstall serve-md`.

### Install from a local clone

```bash
uv tool install .            # add --reinstall to update after pulling changes
```

### Run without installing

```bash
uv run serve-md README.md
```

## Usage

```text
serve-md [-p PORT] [--host HOST] [--browser] file

  file                  path to a .md or .html file
  -p, --port PORT       port to serve on (default: 57642); if taken, the next
                        free port is used
  --host HOST           address to bind (default: 0.0.0.0)
  --browser             open the page in a browser window on start
                        (off by default)
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

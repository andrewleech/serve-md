"""Convert a source file into the HTML page that gets served."""

from __future__ import annotations

from pathlib import Path

import markdown

HTML_SUFFIXES = (".html", ".htm")

RELOAD_JS = """
<script>
(function() {
    let lastMtime = null;
    setInterval(async () => {
        try {
            const r = await fetch('/__mtime');
            const data = await r.json();
            if (lastMtime === null) { lastMtime = data.mtime; return; }
            if (data.mtime !== lastMtime) {
                lastMtime = data.mtime;
                // Preserve scroll position across reload
                sessionStorage.setItem('_scroll', window.scrollY);
                location.reload();
            }
        } catch(e) {}
    }, 500);
    // Restore scroll position after reload
    const saved = sessionStorage.getItem('_scroll');
    if (saved !== null) {
        sessionStorage.removeItem('_scroll');
        window.scrollTo(0, parseInt(saved));
    }
})();
</script>
"""

CSS = """
body {
    max-width: 48em;
    margin: 2em auto;
    padding: 0 1em;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: #e6edf3;
    background: #0d1117;
}
h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; color: #f0f6fc; }
h1 { border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
h2 { border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
code {
    background: #161b22;
    padding: 0.2em 0.4em;
    border-radius: 6px;
    font-size: 85%;
    color: #e6edf3;
}
pre {
    background: #161b22;
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
}
pre code { background: none; padding: 0; font-size: 85%; }
blockquote {
    border-left: 4px solid #30363d;
    margin: 0;
    padding: 0.5em 1em;
    color: #8b949e;
}
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #30363d; padding: 0.4em 0.8em; text-align: left; }
th { background: #161b22; }
img { max-width: 100%; }
hr { border: none; border-top: 1px solid #30363d; margin: 2em 0; }
strong { color: #f0f6fc; }
.codehilite { background: #161b22; padding: 1em; border-radius: 6px; overflow-x: auto; }
"""


def is_html(path: Path) -> bool:
    """Whether ``path`` should be served verbatim rather than rendered."""
    return path.suffix.lower() in HTML_SUFFIXES


def render_markdown(md_path: Path) -> str:
    """Render a Markdown file to a styled, self-contained HTML document."""
    text = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "toc", "smarty"],
        extension_configs={"codehilite": {"css_class": "codehilite", "guess_lang": False}},
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{md_path.name}</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
{RELOAD_JS}
</body>
</html>"""


def render_html(html_path: Path) -> str:
    """Serve an HTML file as-is, injecting the live-reload snippet before ``</body>``."""
    text = html_path.read_text(encoding="utf-8")
    idx = text.lower().rfind("</body>")
    if idx != -1:
        return text[:idx] + RELOAD_JS + text[idx:]
    return text + RELOAD_JS


def render(path: Path) -> str:
    """Render ``path`` to an HTML page, choosing the strategy by file type."""
    return render_html(path) if is_html(path) else render_markdown(path)

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
:root {
    --bg: #0d1117;
    --fg: #e6edf3;
    --heading: #f0f6fc;
    --border: #30363d;
    --link: #58a6ff;
    --surface: #161b22;
    --muted: #8b949e;
}
:root[data-theme="light"] {
    --bg: #ffffff;
    --fg: #1f2328;
    --heading: #1f2328;
    --border: #d1d9e0;
    --link: #0969da;
    --surface: #f6f8fa;
    --muted: #59636e;
}
body {
    width: 90%;
    max-width: none;
    box-sizing: border-box;
    margin: 2em auto;
    padding: 0 1em;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--fg);
    background: var(--bg);
    user-select: text;
    -webkit-user-select: text;
}
h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; color: var(--heading); }
h1 { border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
h2 { border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
    background: var(--surface);
    padding: 0.2em 0.4em;
    border-radius: 6px;
    font-size: 85%;
    color: var(--fg);
}
pre {
    background: var(--surface);
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
}
pre code { background: none; padding: 0; font-size: 85%; }
blockquote {
    border-left: 4px solid var(--border);
    margin: 0;
    padding: 0.5em 1em;
    color: var(--muted);
}
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid var(--border); padding: 0.4em 0.8em; text-align: left; }
th { background: var(--surface); }
img { max-width: 100%; }
hr { border: none; border-top: 1px solid var(--border); margin: 2em 0; }
strong { color: var(--heading); }
/* codehilite token colors (Pygments .k/.s/.c spans) are intentionally left
   unstyled so they inherit --fg and stay legible in both themes. If a Pygments
   stylesheet is ever added, emit both palettes and gate the light one under
   :root[data-theme="light"], as the toggle icons above do. */
.codehilite { background: var(--surface); padding: 1em; border-radius: 6px; overflow-x: auto; }
.theme-toggle {
    position: fixed;
    top: 1em;
    right: 1em;
    width: 2.2em;
    height: 2.2em;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    font-size: 1em;
    line-height: 1;
    color: var(--fg);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    opacity: 0.45;
    transition: opacity 0.15s ease-in-out;
}
.theme-toggle:hover, .theme-toggle:focus-visible { opacity: 1; }
.theme-icon-light { display: none; }
:root[data-theme="light"] .theme-icon-light { display: inline; }
:root[data-theme="light"] .theme-icon-dark { display: none; }
"""

THEME_INIT_JS = """
<script>
(function() {
    try {
        var saved = localStorage.getItem('_theme');
        if (saved === 'light' || saved === 'dark') {
            document.documentElement.setAttribute('data-theme', saved);
        } else if (window.matchMedia &&
                   window.matchMedia('(prefers-color-scheme: light)').matches) {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    } catch (e) {}
})();
</script>
"""

THEME_TOGGLE = """
<button class="theme-toggle" type="button" onclick="_toggleTheme()"
        title="Toggle light/dark theme" aria-label="Toggle light/dark theme">
    <span class="theme-icon-dark">&#x1F319;</span><span class="theme-icon-light">&#x2600;</span>
</button>
<script>
function _toggleTheme() {
    var el = document.documentElement;
    var next = el.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    el.setAttribute('data-theme', next);
    try { localStorage.setItem('_theme', next); } catch (e) {}
}
</script>
"""

CLIPBOARD_JS = """
<script>
(function() {
    function plainText(node, depth) {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;

        let result = '';
        for (const child of node.childNodes) {
            if (child.nodeType === Node.TEXT_NODE) {
                result += child.textContent;
                continue;
            }
            if (child.nodeType !== Node.ELEMENT_NODE) continue;

            if (child.tagName === 'UL' || child.tagName === 'OL') {
                let number = 1;
                for (const item of child.children) {
                    if (item.tagName !== 'LI') continue;
                    const prefix = child.tagName === 'UL' ? '• ' : `${number++}. `;
                    const content = Array.from(item.childNodes)
                        .filter((itemChild) => itemChild.nodeType !== Node.ELEMENT_NODE ||
                            (itemChild.tagName !== 'UL' && itemChild.tagName !== 'OL'))
                        .map((itemChild) => plainText(itemChild, depth + 1))
                        .join('').trim();
                    result += `${'  '.repeat(depth)}${prefix}${content}\\n`;
                    for (const nested of item.children) {
                        if (nested.tagName === 'UL' || nested.tagName === 'OL') {
                            result += plainText(nested, depth + 1);
                        }
                    }
                }
                continue;
            }

            result += plainText(child, depth);
            if (/^(P|DIV|H[1-6]|BLOCKQUOTE|PRE|TR)$/.test(child.tagName)) result += '\\n';
        }
        return result;
    }

    document.addEventListener('copy', (event) => {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;

        const container = document.createElement('div');
        container.append(selection.getRangeAt(0).cloneContents());
        const html = container.innerHTML;
        const text = plainText(container, 0).replace(/\\n{3,}/g, '\\n\\n').trimEnd();
        if (!html || !text) return;

        // Rich-text applications receive native HTML lists and headings. Plain-text
        // applications receive literal bullets and indentation rather than list markers.
        event.preventDefault();
        event.clipboardData.setData('text/html', html);
        event.clipboardData.setData('text/plain', text);
    });
})();
</script>
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
{THEME_INIT_JS}
<style>{CSS}</style>
</head>
<body>
{THEME_TOGGLE}
{html_body}
{CLIPBOARD_JS}
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

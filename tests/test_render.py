"""Tests for the render module."""

from __future__ import annotations

from pathlib import Path

from serve_md.render import RELOAD_JS, is_html, render, render_html, render_markdown


def test_is_html() -> None:
    assert is_html(Path("page.html"))
    assert is_html(Path("page.HTM"))
    assert not is_html(Path("notes.md"))


def test_render_markdown_wraps_body_and_injects_reload(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nSome **bold** text.\n", encoding="utf-8")

    html = render_markdown(md)

    assert "<!DOCTYPE html>" in html
    assert "<title>doc.md</title>" in html
    assert "<h1" in html and "Title" in html
    assert RELOAD_JS.strip() in html


def test_render_html_injects_reload_before_body_close(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text("<html><body><p>hi</p></body></html>", encoding="utf-8")

    html = render_html(page)

    assert html.index(RELOAD_JS.strip()) < html.lower().rindex("</body>")


def test_render_html_without_body_appends_reload(tmp_path: Path) -> None:
    page = tmp_path / "fragment.html"
    page.write_text("<p>no body tag</p>", encoding="utf-8")

    html = render_html(page)

    assert html.endswith(RELOAD_JS)


def test_render_dispatches_by_suffix(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# Heading\n", encoding="utf-8")
    assert "<!DOCTYPE html>" in render(md)

    page = tmp_path / "page.html"
    page.write_text("<body>raw</body>", encoding="utf-8")
    assert "<!DOCTYPE html>" not in render(page)

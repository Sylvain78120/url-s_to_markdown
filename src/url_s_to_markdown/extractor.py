"""Extraction HTML brute: titre + texte dans l'ordre d'apparition."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass
class PageContent:
    url: str
    title: str
    text: str


class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code", "td", "th", "blockquote", "div", "section", "main", "article"}

    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._skip_depth = 0
        self._active_blocks: list[str] = []
        self._current_line_parts: list[str] = []
        self.title = ""
        self._text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

        if self._skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS:
            self._flush_current_line()
            self._active_blocks.append(tag)
            if tag == "li":
                self._current_line_parts.append("- ")
            elif tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
                level = min(max(int(tag[1]), 1), 6)
                self._current_line_parts.append("#" * level + " ")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

        if self._skip_depth > 0:
            return

        if self._active_blocks and tag == self._active_blocks[-1]:
            self._active_blocks.pop()
            self._flush_current_line()

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        cleaned = " ".join(data.split())
        if not cleaned:
            return

        if self._in_title:
            self.title = cleaned
            return

        if self._skip_depth > 0:
            return

        self._current_line_parts.append(cleaned)

    def _flush_current_line(self) -> None:
        if not self._current_line_parts:
            return

        line = " ".join(part.strip() for part in self._current_line_parts if part.strip()).strip()
        self._current_line_parts = []

        if line:
            self._text_chunks.append(line)

    @property
    def text(self) -> str:
        self._flush_current_line()
        return "\n".join(self._text_chunks)


def extract_page_content(url: str, html: str) -> PageContent:
    parser = _TextExtractor()
    parser.feed(html)
    title = parser.title or "Sans titre"
    text = parser.text or "(Contenu texte indisponible)"
    return PageContent(url=url, title=title, text=text)

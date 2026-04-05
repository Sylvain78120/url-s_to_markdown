"""Extraction HTML simple: titre + texte principal."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass
class PageContent:
    url: str
    title: str
    text: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._skip_depth = 0
        self.title = ""
        self._text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title = cleaned
            return
        if self._skip_depth == 0:
            self._text_chunks.append(cleaned)

    @property
    def text(self) -> str:
        return "\n".join(self._text_chunks)


def extract_page_content(url: str, html: str) -> PageContent:
    parser = _TextExtractor()
    parser.feed(html)
    title = parser.title or "Sans titre"
    text = parser.text or "(Contenu texte indisponible)"
    return PageContent(url=url, title=title, text=text)

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
        self._noise_depth = 0
        self._noise_tag_stack: list[str] = []
        self.title = ""
        self._text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

        attr_text = " ".join(str(value).lower() for _, value in attrs if value)
        noisy_attr_hints = ["nav", "menu", "sidebar", "breadcrumb", "footer", "cookie", "toc", "assist"]
        is_noisy = tag in {"nav", "footer", "header", "aside", "form", "button"} or any(
            hint in attr_text for hint in noisy_attr_hints
        )
        if is_noisy:
            self._noise_depth += 1
            self._noise_tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

        if self._noise_tag_stack and tag == self._noise_tag_stack[-1]:
            self._noise_tag_stack.pop()
            if self._noise_depth > 0:
                self._noise_depth -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title = cleaned
            return
        if self._skip_depth > 0 or self._noise_depth > 0:
            return

        lower = cleaned.lower()
        noisy_fragments = [
            "cookie",
            "accept all",
            "privacy policy",
            "subscribe",
            "menu",
            "navigation",
            "skip to main content",
            "was this page helpful",
            "table of contents",
            "back to top",
            "breadcrumbs",
            "assistant",
            "lovable",
            "sign in",
            "get started",
        ]
        if any(fragment in lower for fragment in noisy_fragments):
            return

        self._text_chunks.append(cleaned)

    @property
    def text(self) -> str:
        unique_chunks: list[str] = []
        seen: set[str] = set()
        for chunk in self._text_chunks:
            key = chunk.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique_chunks.append(chunk)
        return "\n".join(unique_chunks)


def extract_page_content(url: str, html: str) -> PageContent:
    parser = _TextExtractor()
    parser.feed(html)
    title = parser.title or "Sans titre"
    text = parser.text or "(Contenu texte indisponible)"
    return PageContent(url=url, title=title, text=text)

"""Détection et découverte de sites de documentation (mode ciblé)."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .http_client import HTTPClient


@dataclass
class DocumentationDiscoveryResult:
    detected: bool
    root_url: str
    urls: list[str]
    section_by_url: dict[str, str]
    signals: list[str]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def _extract_links(base_url: str, html: str) -> list[str]:
    parser = _LinkParser()
    parser.feed(html)
    links: list[str] = []
    for href in parser.links:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        if cleaned:
            links.append(cleaned)
    return links


def _detect_signals(url: str, html: str) -> list[str]:
    signals: list[str] = []
    lower_url = url.lower()
    lower_html = html.lower()

    url_signals = ["/docs", "/documentation", "/guide", "/reference", "/api"]
    if any(sig in lower_url for sig in url_signals):
        signals.append("url_path_doc_like")
    if urlparse(url).netloc.startswith("docs."):
        signals.append("docs_subdomain")

    html_signals = ["table of contents", "sidebar", "was this page helpful", "skip to main content", "breadcrumbs"]
    if any(sig in lower_html for sig in html_signals):
        signals.append("doc_ui_markers")

    if "<nav" in lower_html and "<main" in lower_html:
        signals.append("structured_doc_layout")

    return signals


def _classify_section(url: str) -> str:
    lower = url.lower()
    mapping = {
        "introduction": "Introduction",
        "getting-started": "Getting_started",
        "features": "Features",
        "integrations": "Integrations",
        "reference": "Reference",
        "api": "API",
        "faq": "FAQ",
        "changelog": "Changelog",
        "security": "Security_Privacy",
        "privacy": "Security_Privacy",
        "auth": "Authentication",
        "mcp": "Connectors_MCP",
        "connector": "Connectors_MCP",
        "testing": "Testing",
        "design": "Design",
        "deployment": "Deployment",
    }
    for key, value in mapping.items():
        if key in lower:
            return value
    return "General"


def discover_documentation_urls(
    start_url: str,
    client: HTTPClient,
    *,
    mode: str = "auto",
    max_pages: int = 40,
    max_depth: int = 2,
) -> DocumentationDiscoveryResult:
    try:
        start_html = client.get(start_url)
    except Exception:
        return DocumentationDiscoveryResult(False, start_url, [start_url], {start_url: "General"}, [])

    signals = _detect_signals(start_url, start_html)
    detected = mode == "force" or (mode == "auto" and len(signals) >= 2)
    if mode == "off" or not detected:
        return DocumentationDiscoveryResult(False, start_url, [start_url], {start_url: "General"}, signals)

    parsed_start = urlparse(start_url)
    domain = parsed_start.netloc
    path_parts = [part for part in parsed_start.path.split("/") if part]
    root_prefix = "/"
    for marker in ["docs", "documentation", "guide", "reference", "api"]:
        if marker in path_parts:
            root_prefix = "/" + "/".join(path_parts[: path_parts.index(marker) + 1])
            break
    if root_prefix == "/" and path_parts:
        root_prefix = "/" + path_parts[0]

    queue: list[tuple[str, int]] = [(start_url.rstrip("/"), 0)]
    seen: set[str] = set()
    urls: list[str] = []

    excluded_tokens = ["/blog", "/pricing", "/legal", "/login", "/signin", "/terms", "/privacy", "/about", "/contact"]

    while queue and len(urls) < max_pages:
        current, depth = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)

        parsed = urlparse(current)
        if parsed.netloc != domain:
            continue
        if root_prefix != "/" and not parsed.path.startswith(root_prefix):
            continue
        if any(token in parsed.path.lower() for token in excluded_tokens):
            continue

        urls.append(current)
        if depth >= max_depth:
            continue

        try:
            html = client.get(current)
        except Exception:
            continue

        for link in _extract_links(current, html):
            if link not in seen:
                queue.append((link, depth + 1))

    if not urls:
        urls = [start_url.rstrip("/")]

    section_by_url = {url: _classify_section(url) for url in urls}
    return DocumentationDiscoveryResult(True, start_url, urls, section_by_url, signals)

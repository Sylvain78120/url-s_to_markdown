"""Extraction d'URLs à partir d'un sitemap XML distant."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from .http_client import HTTPClient


@dataclass
class SitemapResult:
    urls: list[str] = field(default_factory=list)
    sitemaps_detected: int = 0
    invalid_urls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _tag_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _extract_loc_values(root: ET.Element) -> list[str]:
    values: list[str] = []
    for elem in root.iter():
        if _tag_name(elem.tag) == "loc":
            value = (elem.text or "").strip()
            if value:
                values.append(value)
    return values


def extract_urls_from_sitemap(
    sitemap_url: str,
    client: HTTPClient,
    *,
    max_depth: int = 2,
    same_domain_only: bool = True,
) -> SitemapResult:
    result = SitemapResult()

    if not _is_valid_url(sitemap_url):
        result.errors.append(f"Sitemap URL invalide: {sitemap_url}")
        return result

    root_domain = urlparse(sitemap_url).netloc
    queue: list[tuple[str, int]] = [(sitemap_url, 0)]
    visited_sitemaps: set[str] = set()
    seen_urls: set[str] = set()

    while queue:
        current_sitemap, depth = queue.pop(0)
        if current_sitemap in visited_sitemaps:
            continue
        visited_sitemaps.add(current_sitemap)
        result.sitemaps_detected += 1

        try:
            xml_content = client.get(current_sitemap)
            root = ET.fromstring(xml_content)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Échec sitemap {current_sitemap}: {type(exc).__name__}: {exc}")
            continue

        root_name = _tag_name(root.tag)
        loc_values = _extract_loc_values(root)

        if root_name == "sitemapindex":
            if depth >= max_depth:
                continue
            for loc in loc_values:
                if _is_valid_url(loc):
                    queue.append((loc, depth + 1))
                else:
                    result.invalid_urls.append(loc)
            continue

        if root_name == "urlset":
            for loc in loc_values:
                if not _is_valid_url(loc):
                    result.invalid_urls.append(loc)
                    continue
                if same_domain_only and urlparse(loc).netloc != root_domain:
                    continue
                if loc in seen_urls:
                    continue
                seen_urls.add(loc)
                result.urls.append(loc)
            continue

        result.errors.append(f"Type de sitemap non supporté pour {current_sitemap}: {root_name}")

    return result

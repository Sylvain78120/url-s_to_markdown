"""Gestion des entrées URL pour la CLI et l'interface web."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class URLStats:
    total_detected: int
    valid_urls: list[str]
    unique_urls: list[str]
    invalid_urls: list[str]


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _collect_candidates(
    single_url: str | None = None,
    urls: list[str] | None = None,
    file_path: str | None = None,
) -> list[str]:
    candidates: list[str] = []

    if single_url:
        candidates.append(single_url.strip())

    if urls:
        candidates.extend(url.strip() for url in urls)

    if file_path:
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
        candidates.extend(line.strip() for line in lines)

    return [candidate for candidate in candidates if candidate]


def parse_url_stats_from_candidates(candidates: list[str]) -> URLStats:
    valid_urls: list[str] = []
    invalid_urls: list[str] = []
    unique_urls: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        if not is_valid_url(candidate):
            invalid_urls.append(candidate)
            continue

        valid_urls.append(candidate)
        if candidate not in seen:
            seen.add(candidate)
            unique_urls.append(candidate)

    return URLStats(
        total_detected=len(candidates),
        valid_urls=valid_urls,
        unique_urls=unique_urls,
        invalid_urls=invalid_urls,
    )


def parse_url_stats(
    single_url: str | None = None,
    urls: list[str] | None = None,
    file_path: str | None = None,
) -> URLStats:
    candidates = _collect_candidates(single_url=single_url, urls=urls, file_path=file_path)
    return parse_url_stats_from_candidates(candidates)


def parse_urls(
    single_url: str | None = None,
    urls: list[str] | None = None,
    file_path: str | None = None,
) -> list[str]:
    """Construit une liste d'URLs propre et dédupliquée."""
    return parse_url_stats(single_url=single_url, urls=urls, file_path=file_path).unique_urls


def parse_urls_from_text_block(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]


def chunk_urls(urls: list[str], max_urls: int) -> list[list[str]]:
    if max_urls <= 0:
        raise ValueError("max_urls doit être > 0")
    return [urls[i : i + max_urls] for i in range(0, len(urls), max_urls)]

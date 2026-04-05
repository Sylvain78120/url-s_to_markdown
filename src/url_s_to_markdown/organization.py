"""Organisation logique des URLs et conventions de nommage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse


@dataclass
class URLGroup:
    key: str
    label: str
    urls: list[str]


def _clean_title(value: str) -> str:
    chars: list[str] = []
    for char in value:
        if char.isalnum():
            chars.append(char)
        else:
            chars.append(" ")
    words = [w for w in "".join(chars).split() if w]
    if not words:
        return "Group"
    return "_".join(word.capitalize() for word in words)


def dated_title(title: str, date_str: str | None = None) -> str:
    prefix = date_str or datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}_{_clean_title(title)}"


def detect_group_label(url: str) -> str:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if len(path_parts) >= 2 and path_parts[0] == "docs":
        return f"Docs_{_clean_title(path_parts[1])}"
    if path_parts and path_parts[0] == "blog":
        return "Blog"
    if path_parts:
        return f"{_clean_title(parsed.netloc)}_{_clean_title(path_parts[0])}"
    return _clean_title(parsed.netloc)


def build_groups(urls: list[str]) -> list[URLGroup]:
    groups: dict[str, URLGroup] = {}
    order: list[str] = []

    for url in urls:
        label = detect_group_label(url)
        key = label.lower()
        if key not in groups:
            groups[key] = URLGroup(key=key, label=label, urls=[])
            order.append(key)
        groups[key].urls.append(url)

    return [groups[key] for key in order]

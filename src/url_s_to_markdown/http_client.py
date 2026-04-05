"""Abstraction HTTP minimale pour faciliter les tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.request import Request, urlopen


class HTTPClient(Protocol):
    def get(self, url: str) -> str:
        """Retourne le HTML brut d'une URL."""


@dataclass
class UrllibHTTPClient:
    timeout_seconds: int = 15

    def get(self, url: str) -> str:
        request = Request(
            url,
            headers={"User-Agent": "url-s-to-markdown/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")

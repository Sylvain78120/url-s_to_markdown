from pathlib import Path

from url_s_to_markdown.sitemap import extract_urls_from_sitemap


class FakeSitemapHTTPClient:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def get(self, url: str) -> str:
        if url not in self.mapping:
            raise RuntimeError("404")
        return self.mapping[url]


def _fixture(name: str) -> str:
    return Path(f"tests/fixtures/{name}").read_text(encoding="utf-8")


def test_parse_urlset_sitemap_and_deduplicate():
    client = FakeSitemapHTTPClient({"https://example.com/sitemap.xml": _fixture("sitemap_urlset.xml")})
    result = extract_urls_from_sitemap("https://example.com/sitemap.xml", client)

    assert result.sitemaps_detected == 1
    assert result.urls == [
        "https://example.com/docs/api/a",
        "https://example.com/docs/api/b",
    ]
    assert "invalid-url" in result.invalid_urls


def test_parse_sitemapindex_and_follow_sub_sitemaps():
    client = FakeSitemapHTTPClient(
        {
            "https://example.com/sitemap.xml": _fixture("sitemap_index.xml"),
            "https://example.com/sitemap-1.xml": _fixture("sitemap_sub_1.xml"),
            "https://example.com/sitemap-2.xml": _fixture("sitemap_sub_2.xml"),
        }
    )
    result = extract_urls_from_sitemap("https://example.com/sitemap.xml", client)

    assert result.sitemaps_detected == 3
    assert "https://example.com/blog/post-1" in result.urls
    assert "https://external.com/x" not in result.urls


def test_sitemap_invalid_xml_is_handled():
    client = FakeSitemapHTTPClient({"https://example.com/sitemap.xml": _fixture("sitemap_invalid.xml")})
    result = extract_urls_from_sitemap("https://example.com/sitemap.xml", client)

    assert result.urls == []
    assert result.errors


def test_sitemap_integration_urls_feed_pipeline_stats():
    client = FakeSitemapHTTPClient(
        {
            "https://example.com/sitemap.xml": _fixture("sitemap_index.xml"),
            "https://example.com/sitemap-1.xml": _fixture("sitemap_sub_1.xml"),
            "https://example.com/sitemap-2.xml": _fixture("sitemap_sub_2.xml"),
        }
    )
    result = extract_urls_from_sitemap(
        "https://example.com/sitemap.xml",
        client,
        same_domain_only=False,
    )

    assert "https://external.com/x" in result.urls
    assert len(result.urls) == 3

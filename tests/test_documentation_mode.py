from url_s_to_markdown.documentation_mode import discover_documentation_urls


class FakeHTTPClient:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def get(self, url: str) -> str:
        return self.mapping[url]


def test_detect_documentation_site_auto_mode():
    mapping = {
        "https://docs.example.com/docs/start": "<html><body><nav>sidebar</nav><main><a href='/docs/api'>API</a><h1>Docs</h1></main></body></html>",
        "https://docs.example.com/docs/api": "<html><body><main><h1>API</h1></main></body></html>",
    }
    result = discover_documentation_urls("https://docs.example.com/docs/start", FakeHTTPClient(mapping), mode="auto")

    assert result.detected is True
    assert "https://docs.example.com/docs/start" in result.urls
    assert "https://docs.example.com/docs/api" in result.urls


def test_exclude_non_documentation_pages_and_keep_scope():
    mapping = {
        "https://example.com/docs": "<html><body><a href='/docs/guide'>Guide</a><a href='/blog/post'>Blog</a></body></html>",
        "https://example.com/docs/guide": "<html><body>Guide</body></html>",
        "https://example.com/blog/post": "<html><body>Blog</body></html>",
    }
    result = discover_documentation_urls("https://example.com/docs", FakeHTTPClient(mapping), mode="force")

    assert "https://example.com/docs/guide" in result.urls
    assert "https://example.com/blog/post" not in result.urls


def test_classification_sections():
    mapping = {
        "https://docs.example.com/docs": "<html><body><a href='/docs/features/x'>F</a><a href='/docs/api/ref'>A</a></body></html>",
        "https://docs.example.com/docs/features/x": "<html><body>x</body></html>",
        "https://docs.example.com/docs/api/ref": "<html><body>y</body></html>",
    }
    result = discover_documentation_urls("https://docs.example.com/docs", FakeHTTPClient(mapping), mode="force")

    assert result.section_by_url["https://docs.example.com/docs/features/x"] == "Features"
    assert result.section_by_url["https://docs.example.com/docs/api/ref"] == "API"

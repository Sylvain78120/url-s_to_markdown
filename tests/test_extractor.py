from pathlib import Path

from url_s_to_markdown.extractor import extract_page_content


def test_extract_page_content_from_local_fixture():
    html = Path("tests/fixtures/sample_page.html").read_text(encoding="utf-8")
    result = extract_page_content(url="https://example.com/page", html=html)

    assert result.title == "Ma page exemple"
    assert "Premier paragraphe." in result.text
    assert "Deuxième paragraphe." in result.text
    assert result.url == "https://example.com/page"
    assert "ignore me" not in result.text

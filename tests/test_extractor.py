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


def test_extract_page_content_filters_common_noise():
    html = """
    <html>
      <head><title>Test bruit</title></head>
      <body>
        <header>Menu principal</header>
        <nav>Navigation</nav>
        <div class="sidebar">Table of contents</div>
        <main>
          <p>Contenu utile A</p>
          <p>Contenu utile B</p>
          <p>Prerequisites: Python 3.10</p>
        </main>
        <footer>Was this page helpful?</footer>
      </body>
    </html>
    """
    result = extract_page_content(url="https://example.com", html=html)

    assert "Contenu utile A" in result.text
    assert "Contenu utile B" in result.text
    assert "Menu principal" not in result.text
    assert "Table of contents" not in result.text
    assert "Was this page helpful" not in result.text
    assert "Prerequisites: Python 3.10" in result.text

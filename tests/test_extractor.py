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


def test_extract_page_content_preserves_order_and_structure():
    html = """
    <html>
      <head><title>Doc brute</title></head>
      <body>
        <h2>Installation</h2>
        <p>Prerequisites: Python 3.10</p>
        <ul>
          <li>Créer un compte</li>
          <li>Configurer la clé API</li>
        </ul>
        <p>Étape 1 : lancer la commande.</p>
      </body>
    </html>
    """
    result = extract_page_content(url="https://example.com", html=html)

    lines = result.text.splitlines()
    assert lines[0] == "## Installation"
    assert "Prerequisites: Python 3.10" in lines[1]
    assert lines[2] == "- Créer un compte"
    assert lines[3] == "- Configurer la clé API"
    assert "Étape 1 : lancer la commande." in lines[4]


def test_extract_page_content_keeps_non_script_text_even_if_noisy():
    html = """
    <html>
      <head><title>Doc</title></head>
      <body>
        <header>Menu principal</header>
        <p>Custom domains</p>
        <p>Labs</p>
        <p>Workspace security center</p>
      </body>
    </html>
    """
    result = extract_page_content(url="https://example.com/doc", html=html)

    assert "Menu principal" in result.text
    assert "Custom domains" in result.text
    assert "Labs" in result.text
    assert "Workspace security center" in result.text

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
          <h2>Installation</h2>
          <p>Prerequisites: Python 3.10</p>
          <ul>
            <li>Créer un compte</li>
            <li>Configurer la clé API</li>
          </ul>
          <p>Étape 1 : lancer la commande.</p>
          <p>Étape 2 : vérifier les logs.</p>
        </main>
        <footer>Was this page helpful?</footer>
      </body>
    </html>
    """
    result = extract_page_content(url="https://example.com", html=html)

    assert "## Installation" in result.text
    assert "Prerequisites: Python 3.10" in result.text
    assert "- Créer un compte" in result.text
    assert "- Configurer la clé API" in result.text
    assert "Étape 1 : lancer la commande." in result.text
    assert "Étape 2 : vérifier les logs." in result.text
    assert "Menu principal" not in result.text
    assert "Table of contents" not in result.text
    assert "Was this page helpful" not in result.text


def test_extract_page_content_removes_orphan_labels_without_truncation():
    html = """
    <html>
      <head><title>Doc</title></head>
      <body>
        <main>
          <p>Custom domains</p>
          <p>Labs</p>
          <p>Workspace security center</p>
          <p>Cette fonctionnalité permet de connecter un domaine personnalisé en 3 étapes.</p>
        </main>
      </body>
    </html>
    """
    result = extract_page_content(url="https://example.com/doc", html=html)

    assert "Custom domains" not in result.text
    assert "Labs" not in result.text
    assert "Workspace security center" not in result.text
    assert "Cette fonctionnalité permet de connecter un domaine personnalisé en 3 étapes." in result.text

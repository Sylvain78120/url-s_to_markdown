from pathlib import Path

from url_s_to_markdown.extractor import PageContent
from url_s_to_markdown.organization import dated_title
from url_s_to_markdown.writers import build_merged_markdown, slugify, write_simple_pdf


def test_slugify_safe_name():
    assert slugify("Hello, World! 2026") == "hello-world-2026"
    assert slugify("   ") == "page"


def test_dated_naming_convention():
    assert dated_title("Docs API", "20260405") == "20260405_Docs_Api"


def test_build_merged_markdown_announces_scope_and_structure():
    pages = [
        PageContent(url="https://a.test", title="Titre A", text="Texte A"),
        PageContent(url="https://b.test", title="Titre B", text="Texte B"),
    ]

    merged = build_merged_markdown(
        pages,
        section_label="Features",
        source_root="https://a.test",
        aggregation_rule="Toutes les pages de la section Features détectées pendant l'extraction.",
        generated_date="2026-04-05",
    )

    assert "# Corpus agrégé — Features" in merged
    assert "Type: agrégé" in merged
    assert "Source racine: https://a.test" in merged
    assert "Nombre de pages incluses: 2" in merged
    assert "## URLs incluses" in merged
    assert "- https://a.test" in merged
    assert "- https://b.test" in merged
    assert "## Page 1 — Titre A" in merged
    assert "## Page 2 — Titre B" in merged
    assert merged.count("---") >= 2


def test_write_simple_pdf_smoke(tmp_path: Path):
    output_pdf = tmp_path / "merged.pdf"
    write_simple_pdf("Ligne 1\nLigne 2", output_pdf)

    content = output_pdf.read_bytes()
    assert output_pdf.exists()
    assert content.startswith(b"%PDF-")
    assert len(content) > 100

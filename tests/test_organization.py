import json
from pathlib import Path

from url_s_to_markdown.organization import build_groups, dated_title, detect_group_label
from url_s_to_markdown.writers import write_organization_markdown


def test_detect_group_label_from_tree():
    assert detect_group_label("https://example.com/docs/api/reference") == "Docs_Api"
    assert detect_group_label("https://example.com/docs/guides/start") == "Docs_Guides"
    assert detect_group_label("https://example.com/blog/post-1") == "Blog"


def test_dated_title_format():
    assert dated_title("Docs API", "20260405") == "20260405_Docs_Api"


def test_build_groups_stable_order():
    groups = build_groups(
        [
            "https://example.com/docs/api/a",
            "https://example.com/blog/a",
            "https://example.com/docs/api/b",
        ]
    )
    assert groups[0].label == "Docs_Api"
    assert groups[1].label == "Blog"
    assert len(groups[0].urls) == 2


def test_organization_plan_md_generation(tmp_path: Path):
    plan = {
        "logic": "test",
        "groups": [{"name": "Docs_Api", "urls": ["https://example.com/docs/api/a"]}],
        "batches": [{"batch_index": 1, "urls": ["https://example.com/docs/api/a"]}],
    }
    path = tmp_path / "organization_plan.md"
    write_organization_markdown(plan, path)
    text = path.read_text(encoding="utf-8")
    assert "Plan d'organisation" in text
    assert "Docs_Api" in text

import json
from pathlib import Path

from url_s_to_markdown.inputs import URLStats
from url_s_to_markdown.pipeline import run_pipeline


class FakeHTTPClient:
    def get(self, url: str) -> str:
        if "fail" in url:
            raise RuntimeError("network down")
        return (
            "<html><head><title>Page test</title></head>"
            "<body><p>Contenu pour " + url + "</p></body></html>"
        )


def _stats(urls: list[str], invalid: list[str] | None = None) -> URLStats:
    invalid = invalid or []
    return URLStats(
        total_detected=len(urls) + len(invalid),
        valid_urls=urls,
        unique_urls=urls,
        invalid_urls=invalid,
    )


def test_run_pipeline_creates_expected_outputs(tmp_path: Path):
    result = run_pipeline(
        stats=_stats(["https://example.com/docs/api/a", "https://openai.com/blog/post"]),
        client=FakeHTTPClient(),
        output_root=tmp_path,
        max_urls=10,
    )

    assert result.output_dir.exists()
    assert result.organization_plan_json.exists()
    assert result.organization_plan_md.exists()
    assert result.manifest_path.exists()
    assert result.errors_log_path.exists()
    assert result.success_count == 2
    assert result.failed_count == 0


def test_run_pipeline_continues_when_url_fails(tmp_path: Path):
    result = run_pipeline(
        stats=_stats(["https://example.com/docs/api/a", "https://fail.example.com/x"]),
        client=FakeHTTPClient(),
        output_root=tmp_path,
        max_urls=10,
    )

    assert result.success_count == 1
    assert result.failed_count == 1
    assert "fail.example.com" in result.errors_log_path.read_text(encoding="utf-8")

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["total_failed"] == 1
    assert manifest["total_succeeded"] == 1


def test_run_pipeline_batches_when_limit_reached(tmp_path: Path):
    urls = [
        "https://a.com/docs/api/1",
        "https://a.com/docs/api/2",
        "https://a.com/docs/api/3",
    ]
    result = run_pipeline(
        stats=_stats(urls),
        client=FakeHTTPClient(),
        output_root=tmp_path,
        max_urls=2,
    )

    assert result.batch_count == 2
    plan = json.loads(result.organization_plan_json.read_text(encoding="utf-8"))
    assert len(plan["batches"]) == 2

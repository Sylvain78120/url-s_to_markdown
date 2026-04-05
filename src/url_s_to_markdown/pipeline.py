"""Pipeline MVP+ : URLs -> groupes .md/.pdf + artefacts optionnels."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .extractor import PageContent, extract_page_content
from .http_client import HTTPClient
from .inputs import URLStats, chunk_urls
from .organization import URLGroup, build_groups, dated_title
from .writers import (
    build_merged_markdown,
    write_group_pages_markdown,
    write_json,
    write_organization_markdown,
    write_simple_pdf,
)


@dataclass
class RunResult:
    output_dir: Path
    batch_count: int
    success_count: int
    failed_count: int
    invalid_count: int
    group_dirs: list[Path]
    generated_files: list[Path]
    manifest_path: Path | None
    errors_log_path: Path | None
    organization_plan_json: Path | None
    organization_plan_md: Path | None


def _group_pdf_title(group: URLGroup, batch_index: int | None) -> str:
    if group.label.lower().startswith("docs_"):
        return group.label
    if group.label.lower() == "blog":
        return "Blog"
    if batch_index is not None:
        return f"Batch_{batch_index:02d}"
    return "Group"


def run_pipeline(
    stats: URLStats,
    client: HTTPClient,
    output_root: Path,
    max_urls: int,
    *,
    include_artifacts: bool = False,
) -> RunResult:
    if not stats.unique_urls:
        raise ValueError("Aucune URL valide fournie.")

    now = datetime.utcnow()
    run_name = f"{now.strftime('%Y%m%d')}_Run_{now.strftime('%H%M%S')}"
    date_str = now.strftime("%Y%m%d")
    output_dir = output_root / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    groups_root = output_dir / "groups"
    errors: list[str] = []
    generated_files: list[Path] = []
    group_dirs: list[Path] = []
    success_count = 0

    batches = chunk_urls(stats.unique_urls, max_urls)
    plan_groups = build_groups(stats.unique_urls)

    organization_plan_json: Path | None = None
    organization_plan_md: Path | None = None
    errors_log_path: Path | None = None
    manifest_path: Path | None = None

    if include_artifacts:
        batch_plan = [{"batch_index": idx + 1, "urls": batch} for idx, batch in enumerate(batches)]
        plan_data = {
            "logic": "Regroupement par branche d'URL: docs/<segment>, blog, sinon domaine + premier segment.",
            "groups": [{"name": group.label, "urls": group.urls} for group in plan_groups],
            "batches": batch_plan,
        }
        organization_plan_json = output_dir / "organization_plan.json"
        organization_plan_md = output_dir / "organization_plan.md"
        write_json(plan_data, organization_plan_json)
        write_organization_markdown(plan_data, organization_plan_md)
        generated_files.extend([organization_plan_json, organization_plan_md])

    for batch_index, batch_urls in enumerate(batches, start=1):
        groups = build_groups(batch_urls)
        for group in groups:
            group_folder_name = dated_title(f"{group.label} Batch {batch_index:02d}", date_str)
            group_dir = groups_root / group_folder_name if include_artifacts else output_dir
            pages_dir = group_dir / "pages"
            group_dir.mkdir(parents=True, exist_ok=True)
            group_dirs.append(group_dir)

            pages: list[PageContent] = []
            for url in group.urls:
                try:
                    html = client.get(url)
                    pages.append(extract_page_content(url=url, html=html))
                    success_count += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"url={url} | error={type(exc).__name__} | message={exc}")

            if not pages:
                continue

            if include_artifacts:
                page_files = write_group_pages_markdown(pages, pages_dir, date_str)
                generated_files.extend(page_files)

            merged_content = build_merged_markdown(pages)
            merged_name = dated_title(group.label, date_str)
            merged_md_path = group_dir / f"{merged_name}.md"
            merged_md_path.write_text(merged_content, encoding="utf-8")
            generated_files.append(merged_md_path)

            pdf_name = dated_title(_group_pdf_title(group, batch_index if len(batches) > 1 else None), date_str)
            merged_pdf_path = group_dir / f"{pdf_name}.pdf"
            write_simple_pdf(merged_content, merged_pdf_path)
            generated_files.append(merged_pdf_path)

    failed_count = len(errors)

    if include_artifacts:
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        errors_log_path = logs_dir / "errors.log"
        errors_log_path.write_text("\n".join(errors) + ("\n" if errors else ""), encoding="utf-8")
        generated_files.append(errors_log_path)

        manifest_data = {
            "total_urls_detected": stats.total_detected,
            "total_valid": len(stats.valid_urls),
            "total_unique": len(stats.unique_urls),
            "total_invalid": len(stats.invalid_urls),
            "total_succeeded": success_count,
            "total_failed": failed_count,
            "batches_created": len(batches),
            "groups_detected": [group.label for group in plan_groups],
            "generated_files": [str(path) for path in generated_files],
        }
        manifest_path = output_dir / "manifest.json"
        write_json(manifest_data, manifest_path)
        generated_files.append(manifest_path)

    return RunResult(
        output_dir=output_dir,
        batch_count=len(batches),
        success_count=success_count,
        failed_count=failed_count,
        invalid_count=len(stats.invalid_urls),
        group_dirs=group_dirs,
        generated_files=generated_files,
        manifest_path=manifest_path,
        errors_log_path=errors_log_path,
        organization_plan_json=organization_plan_json,
        organization_plan_md=organization_plan_md,
    )

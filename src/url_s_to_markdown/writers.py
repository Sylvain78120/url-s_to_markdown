"""Écriture des fichiers markdown et PDF minimal."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .extractor import PageContent
from .organization import dated_title


def slugify(value: str) -> str:
    cleaned = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "page"


def page_to_markdown(page: PageContent) -> str:
    return f"# {page.title}\n\nSource: {page.url}\n\n{page.text}\n"


def build_merged_markdown(pages: list[PageContent]) -> str:
    sections: list[str] = []
    for page in pages:
        sections.append(f"# {page.title}\n\nSource: {page.url}\n\n{page.text}\n")
    return "\n---\n\n".join(sections).strip() + "\n"


def write_group_pages_markdown(pages: list[PageContent], pages_dir: Path, date_str: str) -> list[Path]:
    pages_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for index, page in enumerate(pages, start=1):
        title = f"{index:03d} {page.title}"
        file_path = pages_dir / f"{dated_title(title, date_str)}.md"
        file_path.write_text(page_to_markdown(page), encoding="utf-8")
        paths.append(file_path)

    return paths


def write_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_organization_markdown(plan: dict, path: Path) -> None:
    lines = ["# Plan d'organisation", "", "## Logique", plan.get("logic", ""), "", "## Groupes"]
    for group in plan.get("groups", []):
        lines.append("")
        lines.append(f"### {group['name']}")
        lines.append(f"- URLs: {len(group['urls'])}")
        for url in group["urls"]:
            lines.append(f"  - {url}")
    lines.append("")
    lines.append("## Lots")
    for batch in plan.get("batches", []):
        lines.append(f"- Batch {batch['batch_index']:02d}: {len(batch['urls'])} URL(s)")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _escape_pdf_text(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(text: str, output_path: Path) -> None:
    """Écrit un PDF texte ultra-minimal, suffisant pour un MVP local."""
    lines = [line for line in text.splitlines() if line.strip()] or ["Document vide"]

    max_lines_per_page = 40
    pages = [lines[i : i + max_lines_per_page] for i in range(0, len(lines), max_lines_per_page)]

    objects: list[bytes] = []

    def add_object(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for page_lines in pages:
        stream_lines = [b"BT", b"/F1 11 Tf", b"50 790 Td"]
        first = True
        for line in page_lines:
            escaped = _escape_pdf_text(line).encode("latin-1", errors="replace")
            if not first:
                stream_lines.append(b"0 -14 Td")
            stream_lines.append(b"(" + escaped + b") Tj")
            first = False
        stream_lines.append(b"ET")
        stream = b"\n".join(stream_lines)
        content_id = add_object(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        page_id = add_object(
            b"<< /Type /Page /Parent PAGES_ID 0 R /MediaBox [0 0 595 842] "
            + b"/Resources << /Font << /F1 "
            + str(font_id).encode()
            + b" 0 R >> >> /Contents "
            + str(content_id).encode()
            + b" 0 R >>"
        )
        page_ids.append(page_id)

    kids = b"[ " + b" ".join(str(pid).encode() + b" 0 R" for pid in page_ids) + b" ]"
    pages_id = add_object(b"<< /Type /Pages /Count " + str(len(page_ids)).encode() + b" /Kids " + kids + b" >>")

    for pid in page_ids:
        objects[pid - 1] = objects[pid - 1].replace(b"PAGES_ID", str(pages_id).encode())

    catalog_id = add_object(b"<< /Type /Catalog /Pages " + str(pages_id).encode() + b" 0 R >>")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(("trailer\n" f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n" "startxref\n" f"{xref_pos}\n" "%%EOF\n").encode("ascii"))
    output_path.write_bytes(bytes(pdf))

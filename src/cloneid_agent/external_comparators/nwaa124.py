"""Extraction utilities for the Li et al. NSR 2021 nwaa124 supplement."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import zipfile
from typing import Any
from xml.etree import ElementTree as ET


RECORD_STATUS_LABELS = (
    "structured_numeric_table",
    "model_formula_in_caption_or_methods",
    "embedded_plot_or_representative_image",
    "method_text_only",
    "not_available_in_archive",
    "not_event_linked",
    "not_agent_ready_without_manual_reconstruction",
)

DOCX_EXTRACTION_ENGINE = "python-docx_optional_openxml_fallback"

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class ArchiveSource:
    """Resolved external supplement source."""

    requested_path: str
    resolved_path: Path
    source_type: str
    used_fallback: bool


def _candidate_fallback_paths(requested: Path) -> list[Path]:
    cwd = Path.cwd()
    candidates = [
        cwd / "data" / "nwaa124_supplement_file.zip",
        cwd / "data" / "nwaa124_supplement_file",
        cwd.parent / "cloneid_physicell_agent_codex" / "data" / "nwaa124_supplement_file.zip",
        cwd.parent / "cloneid_physicell_agent_codex" / "data" / "nwaa124_supplement_file",
        Path.home() / "Documents" / "GitHub" / "cloneid_physicell_agent_codex" / "data" / "nwaa124_supplement_file.zip",
        Path.home() / "Documents" / "GitHub" / "cloneid_physicell_agent_codex" / "data" / "nwaa124_supplement_file",
    ]
    if requested.name:
        candidates.extend(
            [
                cwd / requested.name,
                cwd / "data" / requested.name,
                cwd.parent / "cloneid_physicell_agent_codex" / "data" / requested.name,
            ]
        )
    return candidates


def resolve_external_archive_path(external_zip_or_dir: str | Path | None) -> ArchiveSource:
    """Resolve the requested NSR supplement zip or directory.

    The benchmark accepts a zip file or an already-unpacked supplement directory.
    In local Codex runs the uploaded `/mnt/data` path may not be mounted, so the
    known repository data directory is used as a deterministic fallback.
    """

    requested = Path(external_zip_or_dir or "")
    if external_zip_or_dir and requested.exists():
        source_type = "zip" if requested.suffix.lower() == ".zip" else "directory"
        return ArchiveSource(str(external_zip_or_dir), requested, source_type, False)

    for candidate in _candidate_fallback_paths(requested):
        if candidate.exists():
            source_type = "zip" if candidate.suffix.lower() == ".zip" else "directory"
            return ArchiveSource(str(external_zip_or_dir or ""), candidate, source_type, True)

    raise FileNotFoundError(
        "Could not locate the nwaa124 supplement archive or directory. "
        f"Requested: {external_zip_or_dir!r}"
    )


def classify_archive_member(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return "docx"
    if suffix == ".txt":
        return "txt"
    if suffix == ".vcf":
        return "vcf"
    if suffix == ".zip":
        return "zip"
    return "other"


def _inventory_zip(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            rows.append(
                {
                    "path": info.filename,
                    "name": Path(info.filename).name,
                    "size_bytes": info.file_size,
                    "kind": classify_archive_member(info.filename),
                }
            )
    return sorted(rows, key=lambda row: row["path"])


def _inventory_directory(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for member in sorted(path.rglob("*")):
        if not member.is_file():
            continue
        rel = member.relative_to(path).as_posix()
        rows.append(
            {
                "path": rel,
                "name": member.name,
                "size_bytes": member.stat().st_size,
                "kind": classify_archive_member(member),
            }
        )
    return rows


def inventory_external_archive(external_zip_or_dir: str | Path | None) -> dict[str, Any]:
    """List all external archive files and classify docx/txt/vcf members."""

    source = resolve_external_archive_path(external_zip_or_dir)
    files = _inventory_zip(source.resolved_path) if source.source_type == "zip" else _inventory_directory(source.resolved_path)
    counts: dict[str, int] = {}
    for row in files:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1
    return {
        "comparator": "Li et al. National Science Review 2021 nwaa124",
        "requested_path": source.requested_path,
        "resolved_path": str(source.resolved_path),
        "source_type": source.source_type,
        "used_fallback": source.used_fallback,
        "file_count": len(files),
        "kind_counts": counts,
        "files": files,
    }


def materialize_archive(external_zip_or_dir: str | Path | None, work_dir: str | Path) -> Path:
    """Return a directory containing archive members."""

    source = resolve_external_archive_path(external_zip_or_dir)
    if source.source_type == "directory":
        return source.resolved_path

    target = Path(work_dir) / "nwaa124_unpacked"
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source.resolved_path) as archive:
        archive.extractall(target)
    return target


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)).strip()


def _table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for table_row in table.findall(".//w:tr", WORD_NS):
        cells: list[str] = []
        for table_cell in table_row.findall("./w:tc", WORD_NS):
            cell_paragraphs = []
            for paragraph in table_cell.findall(".//w:p", WORD_NS):
                text = _paragraph_text(paragraph)
                if text:
                    cell_paragraphs.append(text)
            cells.append(" ".join(cell_paragraphs).strip())
        rows.append(cells)
    return rows


def _extract_openxml_docx(docx_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ET.fromstring(document_xml)
    body = root.find("w:body", WORD_NS)
    paragraphs: list[str] = []
    tables: list[dict[str, Any]] = []
    document_order: list[dict[str, Any]] = []
    if body is None:
        return {"paragraphs": paragraphs, "tables": tables, "document_order": document_order}

    table_index = 0
    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = _paragraph_text(child)
            if text:
                paragraphs.append(text)
                document_order.append({"type": "paragraph", "text": text})
        elif tag == "tbl":
            table_index += 1
            rows = _table_rows(child)
            tables.append({"table_index": table_index, "rows": rows})
            document_order.append({"type": "table", "table_index": table_index, "rows": rows})

    return {"paragraphs": paragraphs, "tables": tables, "document_order": document_order}


def _extract_with_python_docx(docx_path: Path) -> dict[str, Any] | None:
    try:
        import docx  # type: ignore[import-not-found]
    except Exception:
        return None

    try:
        document = docx.Document(str(docx_path))
    except Exception:
        return None

    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    tables: list[dict[str, Any]] = []
    for idx, table in enumerate(document.tables, start=1):
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        tables.append({"table_index": idx, "rows": rows})
    return {
        "paragraphs": paragraphs,
        "tables": tables,
        "document_order": [],
        "python_docx_available": True,
    }


def _extract_docx_media(docx_path: Path, media_output_dir: Path) -> list[dict[str, Any]]:
    media_rows: list[dict[str, Any]] = []
    media_output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path) as archive:
        for name in archive.namelist():
            if not name.startswith("word/media/"):
                continue
            member_name = Path(name).name
            target = media_output_dir / member_name
            with archive.open(name) as source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            media_rows.append(
                {
                    "archive_path": name,
                    "extracted_path": str(target),
                    "name": member_name,
                    "size_bytes": target.stat().st_size,
                    "record_status": "embedded_plot_or_representative_image",
                }
            )
    return sorted(media_rows, key=lambda row: row["archive_path"])


def extract_docx_payload(docx_path: str | Path, media_output_dir: str | Path) -> dict[str, Any]:
    """Extract docx paragraphs, tables, and embedded media."""

    path = Path(docx_path)
    openxml_payload = _extract_openxml_docx(path)
    python_docx_payload = _extract_with_python_docx(path)
    if python_docx_payload is not None:
        payload = python_docx_payload
        payload["document_order"] = openxml_payload["document_order"]
        engine = "python-docx+openxml_document_order"
    else:
        payload = openxml_payload
        payload["python_docx_available"] = False
        engine = "openxml_fallback"

    media_dir = Path(media_output_dir) / path.stem.replace(" ", "_")
    payload.update(
        {
            "docx_path": str(path),
            "docx_name": path.name,
            "extraction_engine": engine,
            "paragraph_count": len(payload["paragraphs"]),
            "table_count": len(payload["tables"]),
            "embedded_media": _extract_docx_media(path, media_dir),
        }
    )
    payload["embedded_media_count"] = len(payload["embedded_media"])
    return payload


def extract_all_docx_payloads(external_zip_or_dir: str | Path | None, output_dir: str | Path) -> list[dict[str, Any]]:
    """Materialize the archive and extract every docx member."""

    root = materialize_archive(external_zip_or_dir, Path(output_dir) / "_archive_work")
    docx_paths = sorted(root.rglob("*.docx"))
    media_output_dir = Path(output_dir) / "nwaa124_docx_media"
    return [extract_docx_payload(path, media_output_dir) for path in docx_paths]

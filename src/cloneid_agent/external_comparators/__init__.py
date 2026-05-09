"""External publication-level comparator integrations."""

from __future__ import annotations

from .nwaa124 import (
    DOCX_EXTRACTION_ENGINE,
    RECORD_STATUS_LABELS,
    extract_docx_payload,
    inventory_external_archive,
    resolve_external_archive_path,
)

__all__ = [
    "DOCX_EXTRACTION_ENGINE",
    "RECORD_STATUS_LABELS",
    "extract_docx_payload",
    "inventory_external_archive",
    "resolve_external_archive_path",
]

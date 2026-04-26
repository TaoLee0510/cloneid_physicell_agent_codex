"""Typed schema helpers for deterministic CLONEID agent artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


def _expect_type(value: Any, expected_type: type | tuple[type, ...], field_name: str) -> None:
    if not isinstance(value, expected_type):
        expected = (
            ", ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise ValueError(f"{field_name} must be of type {expected}")


def _expect_mapping(value: Any, field_name: str) -> dict[str, Any]:
    _expect_type(value, dict, field_name)
    return value


def _expect_list(value: Any, field_name: str) -> list[Any]:
    _expect_type(value, list, field_name)
    return value


@dataclass(frozen=True)
class QueryRecord:
    name: str
    sql: str
    parameters: dict[str, Any] | None = None
    row_count: int | None = None
    output_file: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QueryRecord":
        mapping = _expect_mapping(payload, "query")
        name = mapping.get("name")
        sql = mapping.get("sql")
        _expect_type(name, str, "query.name")
        _expect_type(sql, str, "query.sql")
        parameters = mapping.get("parameters")
        if parameters is not None:
            _expect_mapping(parameters, "query.parameters")
        row_count = mapping.get("row_count")
        if row_count is not None:
            _expect_type(row_count, int, "query.row_count")
        output_file = mapping.get("output_file")
        if output_file is not None:
            _expect_type(output_file, str, "query.output_file")
        return cls(
            name=name,
            sql=sql,
            parameters=parameters,
            row_count=row_count,
            output_file=output_file,
        )


@dataclass(frozen=True)
class LiveAccess:
    attempted: bool
    success: bool
    error: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LiveAccess":
        mapping = _expect_mapping(payload, "live_access")
        attempted = mapping.get("attempted")
        success = mapping.get("success")
        error = mapping.get("error")
        _expect_type(attempted, bool, "live_access.attempted")
        _expect_type(success, bool, "live_access.success")
        if error is not None:
            _expect_type(error, str, "live_access.error")
        return cls(attempted=attempted, success=success, error=error)


@dataclass(frozen=True)
class DatabaseSummary:
    source: str
    connection_method: str
    database_name: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatabaseSummary":
        mapping = _expect_mapping(payload, "database")
        source = mapping.get("source")
        connection_method = mapping.get("connection_method")
        database_name = mapping.get("database_name")
        _expect_type(source, str, "database.source")
        _expect_type(connection_method, str, "database.connection_method")
        if database_name is not None:
            _expect_type(database_name, str, "database.database_name")
        return cls(
            source=source,
            connection_method=connection_method,
            database_name=database_name,
        )


@dataclass(frozen=True)
class RowCountEntry:
    table: str
    row_count: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RowCountEntry":
        mapping = _expect_mapping(payload, "row_count entry")
        table = mapping.get("table")
        row_count = mapping.get("row_count")
        _expect_type(table, str, "row_count.table")
        _expect_type(row_count, int, "row_count.row_count")
        return cls(table=table, row_count=row_count)


@dataclass(frozen=True)
class DatabaseInventory:
    run_id: str
    generated_at: str
    requested_mode: str
    mode_used: str
    status: str
    live_access: LiveAccess
    database: DatabaseSummary
    tables: list[str]
    table_count: int
    row_counts: list[RowCountEntry]
    fields: dict[str, list[str]]
    key_table_summaries: dict[str, dict[str, Any]]
    queries: list[QueryRecord]
    warnings: list[str]

    REQUIRED_KEY_TABLES = (
        "Passaging",
        "QuPathEvaluation",
        "Perspective",
        "Identity",
        "CellLinesAndPatients",
        "Flask",
        "Media",
        "MediaIngredients",
    )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatabaseInventory":
        mapping = _expect_mapping(payload, "database_inventory")

        run_id = mapping.get("run_id")
        generated_at = mapping.get("generated_at")
        requested_mode = mapping.get("requested_mode")
        mode_used = mapping.get("mode_used")
        status = mapping.get("status")
        _expect_type(run_id, str, "run_id")
        _expect_type(generated_at, str, "generated_at")
        _expect_type(requested_mode, str, "requested_mode")
        _expect_type(mode_used, str, "mode_used")
        _expect_type(status, str, "status")

        if requested_mode not in {"auto", "live", "mock"}:
            raise ValueError("requested_mode must be one of: auto, live, mock")
        if mode_used not in {"live", "mock"}:
            raise ValueError("mode_used must be one of: live, mock")
        if status not in {"ok", "degraded"}:
            raise ValueError("status must be one of: ok, degraded")

        live_access = LiveAccess.from_dict(mapping.get("live_access"))
        database = DatabaseSummary.from_dict(mapping.get("database"))

        tables = _expect_list(mapping.get("tables"), "tables")
        for idx, table in enumerate(tables):
            _expect_type(table, str, f"tables[{idx}]")

        table_count = mapping.get("table_count")
        _expect_type(table_count, int, "table_count")
        if table_count != len(tables):
            raise ValueError("table_count must match len(tables)")

        row_counts_payload = _expect_list(mapping.get("row_counts"), "row_counts")
        row_counts = [RowCountEntry.from_dict(item) for item in row_counts_payload]

        fields_payload = _expect_mapping(mapping.get("fields"), "fields")
        fields: dict[str, list[str]] = {}
        for table_name, field_names in fields_payload.items():
            _expect_type(table_name, str, "fields.<table>")
            _expect_list(field_names, f"fields[{table_name}]")
            for idx, field_name in enumerate(field_names):
                _expect_type(field_name, str, f"fields[{table_name}][{idx}]")
            fields[table_name] = list(field_names)

        summaries = _expect_mapping(mapping.get("key_table_summaries"), "key_table_summaries")
        for table_name in cls.REQUIRED_KEY_TABLES:
            if table_name not in summaries:
                raise ValueError(f"Missing key_table_summaries entry for {table_name}")
            _expect_mapping(summaries[table_name], f"key_table_summaries[{table_name}]")

        queries_payload = _expect_list(mapping.get("queries"), "queries")
        queries = [QueryRecord.from_dict(item) for item in queries_payload]

        warnings_payload = _expect_list(mapping.get("warnings"), "warnings")
        warnings: list[str] = []
        for idx, warning in enumerate(warnings_payload):
            _expect_type(warning, str, f"warnings[{idx}]")
            warnings.append(warning)

        return cls(
            run_id=run_id,
            generated_at=generated_at,
            requested_mode=requested_mode,
            mode_used=mode_used,
            status=status,
            live_access=live_access,
            database=database,
            tables=list(tables),
            table_count=table_count,
            row_counts=row_counts,
            fields=fields,
            key_table_summaries=summaries,
            queries=queries,
            warnings=warnings,
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "DatabaseInventory":
        payload = json.loads(Path(path).read_text())
        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

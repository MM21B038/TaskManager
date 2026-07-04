"""Parse and serialize table JSON documents."""

from __future__ import annotations

import json
import secrets
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TableData:
    name: str
    columns: list[str]
    rows: list[str]
    default: str = ""
    cells: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class TableDocument:
    tables: dict[str, TableData] = field(default_factory=dict)
    schema_version: int = 1

    @classmethod
    def create_new(cls) -> TableDocument:
        return cls(tables={}, schema_version=1)

    @classmethod
    def parse(cls, text: str) -> TableDocument:
        data = json.loads(text)
        tables: dict[str, TableData] = {}
        for table_id, raw in data.get("tables", {}).items():
            tables[table_id] = TableData(
                name=raw["name"],
                columns=list(raw.get("columns", [])),
                rows=list(raw.get("rows", [])),
                default=str(raw.get("default", "")),
                cells={
                    row_key: dict(row_cells)
                    for row_key, row_cells in raw.get("cells", {}).items()
                },
            )
        return cls(tables=tables, schema_version=int(data.get("schema_version", 1)))

    def serialize(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "tables": {
                table_id: {
                    "name": table.name,
                    "columns": table.columns,
                    "rows": table.rows,
                    "default": table.default,
                    "cells": table.cells,
                }
                for table_id, table in self.tables.items()
            },
        }
        return json.dumps(payload, indent=2) + "\n"

    def get_table(self, table_id: str) -> TableData:
        try:
            return self.tables[table_id]
        except KeyError as exc:
            raise ValueError(f"unknown-table:{table_id}") from exc

    def create_table(
        self,
        name: str,
        columns: list[str],
        *,
        rows: list[str] | None = None,
        default_value: str = "",
        initial_rows: list[dict[str, str]] | None = None,
    ) -> tuple[str, TableData]:
        normalized_name = name.strip()
        if any(table.name == normalized_name for table in self.tables.values()):
            raise ValueError(normalized_name)

        table_id = _new_table_id()
        table = TableData(
            name=normalized_name,
            columns=_normalize_columns(columns),
            rows=[],
            default=default_value,
            cells={},
        )

        if rows:
            self._add_rows_to_table(table, rows, default_value=default_value)

        if initial_rows:
            for row_data in initial_rows:
                row_key = row_data.get("row", "").strip()
                if not row_key:
                    raise ValueError("initial_rows entries must include a non-empty 'row' key")
                if row_key not in table.rows:
                    table.rows.append(row_key)
                    table.cells.setdefault(row_key, {})
                self._apply_row_values(table, row_key, row_data, default_value=None)

        self.tables[table_id] = table
        return table_id, table

    def add_rows(
        self,
        table_id: str,
        rows: list[str],
        *,
        default_value: str | None = None,
        values: list[dict[str, str]] | None = None,
    ) -> TableData:
        table = self.get_table(table_id)
        fill = table.default if default_value is None else default_value
        self._add_rows_to_table(table, rows, default_value=fill)

        if values:
            for row_data in values:
                row_key = row_data.get("row", "").strip()
                if not row_key:
                    raise ValueError("values entries must include a non-empty 'row' key")
                if row_key not in table.rows:
                    raise ValueError(f"unknown-row:{row_key}")
                self._apply_row_values(table, row_key, row_data, default_value=None)

        return table

    def add_columns(
        self,
        table_id: str,
        columns: list[str],
        *,
        default_value: str | None = None,
    ) -> TableData:
        table = self.get_table(table_id)
        fill = table.default if default_value is None else default_value
        for column in _normalize_columns(columns):
            if column in table.columns:
                raise ValueError(column)
            table.columns.append(column)
            for row_key in table.rows:
                row_cells = table.cells.setdefault(row_key, {})
                row_cells.setdefault(column, fill)
        return table

    def apply_updates(
        self,
        table_id: str,
        updates: list[dict[str, Any]] | None = None,
        matrix: list[dict[str, Any]] | None = None,
    ) -> TableData:
        table = self.get_table(table_id)

        if updates and matrix:
            raise ValueError("Provide either updates or matrix, not both")

        if matrix is not None:
            for row_data in matrix:
                row_key = str(row_data.get("row", "")).strip()
                if not row_key:
                    raise ValueError("matrix entries must include a non-empty 'row' key")
                if row_key not in table.rows:
                    raise ValueError(f"unknown-row:{row_key}")
                values = row_data.get("values")
                if not isinstance(values, dict):
                    raise ValueError("matrix entries must include a 'values' object")
                self._apply_row_values(table, row_key, values, default_value=None)
            return table

        for update in updates or []:
            self._apply_update(table, update)

        return table

    def resolve_cells(
        self,
        table: TableData,
        *,
        rows: list[str] | None = None,
        columns: list[str] | None = None,
        resolved: bool = True,
    ) -> dict[str, dict[str, str]]:
        selected_rows = rows if rows is not None else table.rows
        selected_columns = columns if columns is not None else table.columns

        for row_key in selected_rows:
            if row_key not in table.rows:
                raise ValueError(f"unknown-row:{row_key}")
        for column in selected_columns:
            if column not in table.columns:
                raise ValueError(f"unknown-column:{column}")

        result: dict[str, dict[str, str]] = {}
        for row_key in selected_rows:
            row_cells = table.cells.get(row_key, {})
            result[row_key] = {}
            for column in selected_columns:
                if resolved:
                    result[row_key][column] = row_cells.get(column, table.default)
                elif column in row_cells:
                    result[row_key][column] = row_cells[column]
        return result

    def _add_rows_to_table(
        self,
        table: TableData,
        rows: list[str],
        *,
        default_value: str,
    ) -> None:
        for row_key in rows:
            normalized = row_key.strip()
            if not normalized:
                raise ValueError("row keys must be non-empty strings")
            if normalized in table.rows:
                raise ValueError(normalized)
            table.rows.append(normalized)
            table.cells[normalized] = {
                column: default_value for column in table.columns
            }

    def _apply_update(self, table: TableData, update: dict[str, Any]) -> None:
        row = update.get("row")
        column = update.get("column")
        value = update.get("value")
        values = update.get("values")

        if row is not None and column is not None and value is not None and values is None:
            self._set_cell(table, str(row), str(column), str(value))
            return

        if row is not None and values is not None and column is None and value is None:
            row_key = str(row)
            if row_key not in table.rows:
                raise ValueError(f"unknown-row:{row_key}")
            if not isinstance(values, dict):
                raise ValueError("values must be an object")
            self._apply_row_values(table, row_key, values, default_value=None)
            return

        if row is not None and value is not None and column is None and values is None:
            row_key = str(row)
            if row_key not in table.rows:
                raise ValueError(f"unknown-row:{row_key}")
            for column_name in table.columns:
                self._set_cell(table, row_key, column_name, str(value))
            return

        if column is not None and value is not None and row is None and values is None:
            column_name = str(column)
            if column_name not in table.columns:
                raise ValueError(f"unknown-column:{column_name}")
            for row_key in table.rows:
                self._set_cell(table, row_key, column_name, str(value))
            return

        raise ValueError("Invalid update item")

    def _apply_row_values(
        self,
        table: TableData,
        row_key: str,
        values: dict[str, Any],
        *,
        default_value: str | None,
    ) -> None:
        row_cells = table.cells.setdefault(row_key, {})
        for key, raw_value in values.items():
            if key == "row":
                continue
            if key not in table.columns:
                raise ValueError(f"unknown-column:{key}")
            row_cells[key] = str(raw_value) if raw_value is not None else (
                table.default if default_value is None else default_value
            )

    def _set_cell(self, table: TableData, row_key: str, column_name: str, value: str) -> None:
        if row_key not in table.rows:
            raise ValueError(f"unknown-row:{row_key}")
        if column_name not in table.columns:
            raise ValueError(f"unknown-column:{column_name}")
        table.cells.setdefault(row_key, {})[column_name] = value


def _new_table_id() -> str:
    return f"tbl-{secrets.token_hex(4)}"


def _normalize_columns(columns: list[str]) -> list[str]:
    normalized: list[str] = []
    for column in columns:
        name = column.strip()
        if not name:
            raise ValueError("column names must be non-empty strings")
        if name in normalized:
            raise ValueError(name)
        normalized.append(name)
    return normalized

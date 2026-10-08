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
        if not normalized_name:
            raise ValueError("table name must be a non-empty string")
        if any(table.name == normalized_name for table in self.tables.values()):
            raise _coded_error("duplicate-table", normalized_name)

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
                self._apply_row_values(table, row_key, row_data)

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
                self._apply_row_values(table, row_key, row_data)

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
                raise _coded_error("duplicate-column", table.name, column)
            table.columns.append(column)
            for row_key in table.rows:
                row_cells = table.cells.setdefault(row_key, {})
                row_cells.setdefault(column, fill)
        return table

    def delete_table(self, table_id: str) -> None:
        if table_id not in self.tables:
            raise ValueError(f"unknown-table:{table_id}")
        del self.tables[table_id]

    def remove_rows(self, table_id: str, rows: list[str]) -> TableData:
        table = self.get_table(table_id)
        names = _unique_existing_keys(rows, existing=table.rows, kind="row")
        for name in names:
            table.rows.remove(name)
            table.cells.pop(name, None)
        return table

    def remove_columns(self, table_id: str, columns: list[str]) -> TableData:
        table = self.get_table(table_id)
        names = _unique_existing_keys(columns, existing=table.columns, kind="column")
        for name in names:
            table.columns.remove(name)
            for row_cells in table.cells.values():
                row_cells.pop(name, None)
        return table

    def rename_table(self, table_id: str, name: str) -> TableData:
        table = self.get_table(table_id)
        normalized = name.strip()
        if not normalized:
            raise ValueError("table name must be a non-empty string")
        if any(
            other.name == normalized and other_id != table_id
            for other_id, other in self.tables.items()
        ):
            raise _coded_error("duplicate-table", normalized)
        table.name = normalized
        return table

    def rename_row(self, table_id: str, row: str, new_row: str) -> TableData:
        table = self.get_table(table_id)
        if row not in table.rows:
            raise ValueError(f"unknown-row:{row}")
        normalized = new_row.strip()
        if not normalized:
            raise ValueError("row keys must be non-empty strings")
        if normalized != row and normalized in table.rows:
            raise _coded_error("duplicate-row", table.name, normalized)
        index = table.rows.index(row)
        table.rows[index] = normalized
        table.cells[normalized] = table.cells.pop(row, {})
        return table

    def rename_column(self, table_id: str, column: str, new_column: str) -> TableData:
        table = self.get_table(table_id)
        if column not in table.columns:
            raise ValueError(f"unknown-column:{column}")
        normalized = new_column.strip()
        if not normalized:
            raise ValueError("column names must be non-empty strings")
        if normalized != column and normalized in table.columns:
            raise _coded_error("duplicate-column", table.name, normalized)
        index = table.columns.index(column)
        table.columns[index] = normalized
        for row_key, row_cells in list(table.cells.items()):
            rebuilt: dict[str, str] = {}
            for key, raw_value in row_cells.items():
                rebuilt[normalized if key == column else key] = raw_value
            table.cells[row_key] = rebuilt
        return table

    def apply_updates(
        self,
        table_id: str,
        updates: list[dict[str, Any]] | None = None,
        matrix: list[dict[str, Any]] | None = None,
    ) -> int:
        table = self.get_table(table_id)

        if updates and matrix:
            raise ValueError("Provide either updates or matrix, not both")

        if matrix:
            written = 0
            for row_data in matrix:
                row_key = str(row_data.get("row", "")).strip()
                if not row_key:
                    raise ValueError("matrix entries must include a non-empty 'row' key")
                if row_key not in table.rows:
                    raise ValueError(f"unknown-row:{row_key}")
                values = row_data.get("values")
                if not isinstance(values, dict):
                    raise ValueError("matrix entries must include a 'values' object")
                written += self._apply_row_values(table, row_key, values)
            return written

        if updates:
            written = 0
            for update in updates:
                written += self._apply_update(table, update)
            return written

        raise ValueError(_EMPTY_SET_CELLS)

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
        seen: set[str] = set()
        for row_key in rows:
            normalized = row_key.strip()
            if not normalized:
                raise ValueError("row keys must be non-empty strings")
            if normalized in seen:
                raise _coded_error("duplicated-row", normalized)
            seen.add(normalized)
            if normalized in table.rows:
                raise _coded_error("duplicate-row", table.name, normalized)
            table.rows.append(normalized)
            table.cells[normalized] = {
                column: default_value for column in table.columns
            }

    def _apply_update(self, table: TableData, update: dict[str, Any]) -> int:
        row = update.get("row")
        column = update.get("column")
        has_value = "value" in update
        value = update.get("value")
        values = update.get("values")

        if has_value and not isinstance(value, str):
            raise ValueError(_NULL_VALUE_ERROR)
        if isinstance(values, dict) and any(not isinstance(raw, str) for raw in values.values()):
            raise ValueError(_NULL_VALUE_ERROR)

        if row is not None and column is not None and has_value and values is None:
            self._set_cell(table, str(row), str(column), str(value))
            return 1

        if row is not None and values is not None and column is None and not has_value:
            row_key = str(row)
            if row_key not in table.rows:
                raise ValueError(f"unknown-row:{row_key}")
            if not isinstance(values, dict):
                raise ValueError("values must be an object")
            return self._apply_row_values(table, row_key, values)

        if row is not None and has_value and column is None and values is None:
            row_key = str(row)
            if row_key not in table.rows:
                raise ValueError(f"unknown-row:{row_key}")
            for column_name in table.columns:
                self._set_cell(table, row_key, column_name, str(value))
            return len(table.columns)

        if column is not None and has_value and row is None and values is None:
            column_name = str(column)
            if column_name not in table.columns:
                raise ValueError(f"unknown-column:{column_name}")
            for row_key in table.rows:
                self._set_cell(table, row_key, column_name, str(value))
            return len(table.rows)

        raise ValueError("Invalid update item")

    def _apply_row_values(
        self,
        table: TableData,
        row_key: str,
        values: dict[str, Any],
    ) -> int:
        row_cells = table.cells.setdefault(row_key, {})
        written = 0
        for key, raw_value in values.items():
            if key == "row":
                continue
            if key not in table.columns:
                raise ValueError(f"unknown-column:{key}")
            if not isinstance(raw_value, str):
                raise ValueError(_NULL_VALUE_ERROR)
            row_cells[key] = raw_value
            written += 1
        return written

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
            raise _coded_error("duplicated-column", name)
        normalized.append(name)
    return normalized


_EMPTY_SET_CELLS = "set_cells requires a non-empty updates list or a non-empty matrix"
_NULL_VALUE_ERROR = "value must be a string; pass an empty string to store a blank cell"


def _coded_error(code: str, *parts: str) -> ValueError:
    return ValueError(f"{code}:{json.dumps(list(parts), ensure_ascii=False)}")


def _unique_existing_keys(names: list[str], *, existing: list[str], kind: str) -> list[str]:
    if not names:
        label = "rows" if kind == "row" else "columns"
        raise ValueError(f"{label} must be a non-empty list")
    empty_message = (
        "row keys must be non-empty strings"
        if kind == "row"
        else "column names must be non-empty strings"
    )
    unknown_prefix = "unknown-row" if kind == "row" else "unknown-column"
    selected: list[str] = []
    for raw in names:
        name = raw.strip()
        if not name:
            raise ValueError(empty_message)
        if name not in existing:
            raise ValueError(f"{unknown_prefix}:{name}")
        if name not in selected:
            selected.append(name)
    return selected

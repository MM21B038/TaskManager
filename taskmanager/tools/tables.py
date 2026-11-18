"""Table MCP tools."""

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import BeforeValidator

from taskmanager.models import CellUpdate, RowMatrix, SeedRow
from taskmanager.tools._helpers import get_service, map_errors


def _normalize_values(raw: Any) -> Any:
    """Accept {"row": {col: val}} or a single row object in place of a list of row objects."""
    if not isinstance(raw, dict):
        return raw
    if isinstance(raw.get("row"), str):
        return [raw]
    if raw and all(isinstance(v, dict) for v in raw.values()):
        return [{**cells, "row": key} for key, cells in raw.items()]
    return raw


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def table_create(
        task_id: str,
        name: str,
        columns: list[str],
        rows: list[str] | None = None,
        default_value: str = "",
        initial_rows: list[SeedRow] | None = None,
    ):
        """Create a named table with columns, optional rows, and optional seed cell values.

        Each initial_rows item must include a non-empty row key. Every other key is a column
        name mapped to a string cell value, for example {"row": "users", "status": "done"}.
        """
        return get_service().table_create(
            task_id,
            name,
            columns,
            rows=rows,
            default_value=default_value,
            initial_rows=[row.model_dump() for row in initial_rows] if initial_rows else None,
        )

    @mcp.tool()
    @map_errors
    def table_list(task_id: str):
        """List tables in a table-mode task with row/column counts."""
        return get_service().table_list(task_id)

    @mcp.tool()
    @map_errors
    def table_get(
        task_id: str,
        table_id: str,
        rows: list[str] | None = None,
        columns: list[str] | None = None,
        resolved: bool = True,
    ):
        """Get a table, optionally sliced by rows and columns.

        When rows or columns is provided, those response lists match the slice in request
        order. Omitting a filter returns the full axis. resolved=true fills missing cells
        with the table default.
        """
        return get_service().table_get(
            task_id,
            table_id,
            rows=rows,
            columns=columns,
            resolved=resolved,
        )

    @mcp.tool()
    @map_errors
    def table_add_rows(
        task_id: str,
        table_id: str,
        rows: list[str | SeedRow],
        default_value: str | None = None,
        values: Annotated[list[SeedRow] | None, BeforeValidator(_normalize_values)] = None,
    ):
        """Add rows to a table, optionally seeding per-row cell values.

        rows is a list of row-key strings, e.g. ["https://example.com/"]. To seed cells, pass
        values as a list of objects, each with a non-empty "row" key plus column-name keys, e.g.
        [{"row": "https://example.com/", "status_code": "200"}]. Cell values must be strings.
        """
        row_keys: list[str] = []
        seeded: list[dict[str, str]] = []
        for item in rows:
            if isinstance(item, str):
                row_keys.append(item)
                continue
            data = item.model_dump()
            row_keys.append(data["row"])
            if len(data) > 1:
                seeded.append(data)
        seeded.extend(row.model_dump() for row in values or [])
        return get_service().table_add_rows(
            task_id,
            table_id,
            row_keys,
            default_value=default_value,
            values=seeded or None,
        )

    @mcp.tool()
    @map_errors
    def table_add_columns(
        task_id: str,
        table_id: str,
        columns: list[str],
        default_value: str | None = None,
    ):
        """Add columns to a table, filling existing rows with the default value."""
        return get_service().table_add_columns(
            task_id,
            table_id,
            columns,
            default_value=default_value,
        )

    @mcp.tool()
    @map_errors
    def table_set_cells(
        task_id: str,
        table_id: str,
        updates: list[CellUpdate] | None = None,
        matrix: list[RowMatrix] | None = None,
    ):
        """Update table cell values via sparse updates or a row matrix.

        Provide updates or matrix, not both, and not an empty list.
        Update shapes: single cell {row, column, value}; partial row {row, values};
        fill row {row, value}; fill column {column, value}.
        Matrix items require row plus values (column name to string). Omitted columns stay
        unchanged. value must be a string; null is rejected. An empty string stores a blank cell.
        updated_count is the number of cells written. op_count is the number of update items
        or matrix rows.
        """
        return get_service().table_set_cells(
            task_id,
            table_id,
            updates=updates,
            matrix=matrix,
        )

    @mcp.tool()
    @map_errors
    def table_delete(task_id: str, table_id: str):
        """Delete one table from a table-mode task."""
        return get_service().table_delete(task_id, table_id)

    @mcp.tool()
    @map_errors
    def table_remove_rows(task_id: str, table_id: str, rows: list[str]):
        """Remove row keys and their cells from a table."""
        return get_service().table_remove_rows(task_id, table_id, rows)

    @mcp.tool()
    @map_errors
    def table_remove_columns(task_id: str, table_id: str, columns: list[str]):
        """Remove columns and their cells from a table."""
        return get_service().table_remove_columns(task_id, table_id, columns)

    @mcp.tool()
    @map_errors
    def table_rename(task_id: str, table_id: str, name: str):
        """Rename a table. Row keys, column names, and cells stay unchanged."""
        return get_service().table_rename(task_id, table_id, name)

    @mcp.tool()
    @map_errors
    def table_rename_row(task_id: str, table_id: str, row: str, new_row: str):
        """Rename a row key, preserving its position and cell values."""
        return get_service().table_rename_row(task_id, table_id, row, new_row)

    @mcp.tool()
    @map_errors
    def table_rename_column(task_id: str, table_id: str, column: str, new_column: str):
        """Rename a column, preserving its position and cell values."""
        return get_service().table_rename_column(task_id, table_id, column, new_column)

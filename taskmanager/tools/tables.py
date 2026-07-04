"""Table MCP tools."""

from fastmcp import FastMCP

from taskmanager.models import CellUpdate, RowMatrix
from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def table_create(
        task_id: str,
        name: str,
        columns: list[str],
        rows: list[str] | None = None,
        default_value: str = "",
        initial_rows: list[dict[str, str]] | None = None,
    ):
        """Create a named table with columns, optional rows, and optional seed cell values."""
        return get_service().table_create(
            task_id,
            name,
            columns,
            rows=rows,
            default_value=default_value,
            initial_rows=initial_rows,
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
        """Get a table, optionally sliced by rows/columns. resolved=true fills missing cells with defaults."""
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
        rows: list[str],
        default_value: str | None = None,
        values: list[dict[str, str]] | None = None,
    ):
        """Add rows to a table, optionally seeding per-row cell values."""
        return get_service().table_add_rows(
            task_id,
            table_id,
            rows,
            default_value=default_value,
            values=values,
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
        """Update table cell values via sparse updates or a row matrix. Provide updates or matrix, not both."""
        return get_service().table_set_cells(
            task_id,
            table_id,
            updates=updates,
            matrix=matrix,
        )

"""Report section MCP tools."""

from fastmcp import FastMCP
from fastmcp.types import Textarea

from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def set_report(task_id: str, report: Textarea):
        """Replace the report section for a task."""
        return get_service().set_report(task_id, report)

    @mcp.tool()
    @map_errors
    def get_report(task_id: str):
        """Read the report section for a task."""
        return get_service().get_report(task_id)

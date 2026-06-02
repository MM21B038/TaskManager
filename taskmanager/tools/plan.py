"""Plan section MCP tools."""

from fastmcp import FastMCP
from fastmcp.types import Textarea

from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def set_plan(task_id: str, plan: Textarea):
        """Replace the plan section for a task."""
        return get_service().set_plan(task_id, plan)

    @mcp.tool()
    @map_errors
    def get_plan(task_id: str):
        """Read the plan section for a task."""
        return get_service().get_plan(task_id)

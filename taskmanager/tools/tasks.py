"""Task lifecycle MCP tools."""

from typing import Literal

from fastmcp import FastMCP
from fastmcp.types import Textarea

from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def create_task(
        name: str,
        description: str,
        mode: Literal["todo", "table"] = "todo",
        initial_plan: Textarea = "",
        initial_todos: list[str] | None = None,
    ):
        """Create a new task with metadata, plan/todos/report sections, and an empty rough-notes file."""
        return get_service().create_task(
            name,
            description,
            mode=mode,
            initial_plan=initial_plan or "",
            initial_todos=initial_todos,
        )

    @mcp.tool()
    @map_errors
    def get_task(task_id: str):
        """Return full task: metadata, plan, todos, and report."""
        return get_service().get_task(task_id)

    @mcp.tool()
    @map_errors
    def get_task_metadata(task_id: str):
        """Return task metadata (frontmatter) only."""
        return get_service().get_task_metadata(task_id)

    @mcp.tool()
    @map_errors
    def list_tasks():
        """List all tasks with summary counts."""
        return get_service().list_tasks()

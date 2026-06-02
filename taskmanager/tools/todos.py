"""Todo MCP tools."""

from fastmcp import FastMCP

from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def add_todos(task_id: str, items: list[str]):
        """Append todo items; returns assigned todo ids."""
        return get_service().add_todos(task_id, items)

    @mcp.tool()
    @map_errors
    def toggle_todo(task_id: str, todo_id: str, completed: bool | None = None):
        """Toggle or set todo completion. Pass completed=null to flip."""
        return get_service().toggle_todo(task_id, todo_id, completed=completed)

    @mcp.tool()
    @map_errors
    def update_todo(task_id: str, todo_id: str, text: str):
        """Update todo label text."""
        return get_service().update_todo(task_id, todo_id, text)

    @mcp.tool()
    @map_errors
    def remove_todo(task_id: str, todo_id: str):
        """Remove a todo item."""
        get_service().remove_todo(task_id, todo_id)
        return {"task_id": task_id, "todo_id": todo_id, "removed": True}

    @mcp.tool()
    @map_errors
    def get_todos(task_id: str):
        """List todos with completion status."""
        return get_service().get_todos(task_id)

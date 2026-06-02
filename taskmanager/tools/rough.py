"""Rough notes MCP tools."""

from fastmcp import FastMCP
from fastmcp.types import Textarea

from taskmanager.tools._helpers import get_service, map_errors


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    @map_errors
    def rough_add(task_id: str, content: Textarea, note_id: str | None = None):
        """Add a rough note block. Optional note_id must be unique."""
        return get_service().rough_add(task_id, content, note_id=note_id)

    @mcp.tool()
    @map_errors
    def rough_update(task_id: str, note_id: str, content: Textarea):
        """Update an existing rough note by id."""
        return get_service().rough_update(task_id, note_id, content)

    @mcp.tool()
    @map_errors
    def rough_delete(task_id: str, note_id: str):
        """Delete a rough note by id."""
        get_service().rough_delete(task_id, note_id)
        return {"task_id": task_id, "note_id": note_id, "deleted": True}

    @mcp.tool()
    @map_errors
    def rough_get(task_id: str, note_id: str):
        """Get a single rough note by id."""
        return get_service().rough_get(task_id, note_id)

    @mcp.tool()
    @map_errors
    def rough_list(task_id: str):
        """List all rough notes with previews."""
        return get_service().rough_list(task_id)

    @mcp.tool()
    @map_errors
    def rough_clear(task_id: str):
        """Remove all rough notes for a task."""
        return get_service().rough_clear(task_id)

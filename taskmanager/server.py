"""FastMCP server instance."""

from fastmcp import FastMCP

from taskmanager.platform import server_lifespan
from taskmanager.tools import register_all

mcp = FastMCP(
    "Task Manager",
    instructions=(
        "Manage agent tasks stored as markdown. Workflow: create_task → set_plan / "
        "add_todos → rough_add for scratch notes → toggle_todo as work completes → "
        "set_report for the final summary."
    ),
    lifespan=server_lifespan,
)

register_all(mcp)

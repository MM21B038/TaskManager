"""FastMCP server instance."""

from fastmcp import FastMCP

from taskmanager.platform import server_lifespan
from taskmanager.resources import register as register_resources
from taskmanager.tools import register_all

mcp = FastMCP(
    "Task Manager",
    instructions=(
        "Manage agent tasks stored as markdown. Use for substantive multi-step work only — "
        "not trivial one-shot requests. Supports todo checklist mode and table matrix mode. "
        "Loop: Setup → work/rough/progress → Finish. See MCP prompt agent_system_prompt."
    ),
    lifespan=server_lifespan,
)

register_all(mcp)
register_resources(mcp)

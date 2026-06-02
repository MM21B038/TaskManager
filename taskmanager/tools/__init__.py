"""MCP tool registration."""

from fastmcp import FastMCP

from taskmanager.tools import plan, report, rough, tasks, todos


def register_all(mcp: FastMCP) -> None:
    tasks.register(mcp)
    plan.register(mcp)
    todos.register(mcp)
    report.register(mcp)
    rough.register(mcp)

"""MCP resource registration."""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import FileResource

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "agent-system-prompt.md"
_SYSTEM_PROMPT_URI = "taskmanager://agent-system-prompt"


def register(mcp: FastMCP) -> None:
    mcp.add_resource(
        FileResource(
            uri=_SYSTEM_PROMPT_URI,
            path=_SYSTEM_PROMPT_PATH,
            name="Agent system prompt",
            description=(
                "Instructions for using Task Manager MCP tools: lifecycle, when to call each tool, "
                "and workflow rules. Copy into agent system instructions or a Cursor rule."
            ),
            mime_type="text/markdown",
            tags={"documentation", "prompt"},
        )
    )

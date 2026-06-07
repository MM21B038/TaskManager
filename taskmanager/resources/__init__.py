"""MCP resource and prompt registration."""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import FileResource

from taskmanager import __version__

RESOURCES_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = RESOURCES_DIR / "agent-system-prompt.md"
SERVER_INFO_PATH = RESOURCES_DIR / "server-info.md"
SERVER_INFO_URI = "taskmanager://server-info"
SYSTEM_PROMPT_NAME = "agent_system_prompt"


def _read_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def register(mcp: FastMCP) -> None:
    mcp.add_resource(
        FileResource(
            uri=SERVER_INFO_URI,
            path=SERVER_INFO_PATH,
            name="Server info",
            description=(
                "Task Manager MCP server overview: endpoints, storage, environment, "
                f"tools, and workflow (v{__version__})."
            ),
            mime_type="text/markdown",
            tags={"documentation", "server"},
        )
    )

    @mcp.prompt(
        name=SYSTEM_PROMPT_NAME,
        description=(
            "Agent instructions for Task Manager: workflow, rough notes, todos, and report. "
            "Use as system or developer context when working with this MCP server."
        ),
        tags={"documentation", "agent"},
    )
    def agent_system_prompt() -> str:
        """Task Manager agent system instructions."""
        return _read_system_prompt()

"""MCP server-info resource and agent_system_prompt registration."""

import asyncio

from taskmanager.resources import SERVER_INFO_PATH, SERVER_INFO_URI, SYSTEM_PROMPT_PATH
from taskmanager.server import mcp


def test_resource_files_exist():
    assert SYSTEM_PROMPT_PATH.is_file()
    assert SERVER_INFO_PATH.is_file()
    assert SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    assert SERVER_INFO_PATH.read_text(encoding="utf-8").strip()


def test_server_info_and_agent_prompt_registered():
    async def _check():
        prompts = await mcp.list_prompts()
        names = {p.name for p in prompts}
        assert "agent_system_prompt" in names

        resources = await mcp.list_resources()
        uris = {str(r.uri) for r in resources}
        assert SERVER_INFO_URI in uris
        assert "taskmanager://agent-system-prompt" not in uris

        result = await mcp.render_prompt("agent_system_prompt", {})
        text = "".join(
            m.content.text
            for m in result.messages
            if hasattr(m.content, "text")
        )
        assert "Task Manager MCP server" in text

    asyncio.run(_check())

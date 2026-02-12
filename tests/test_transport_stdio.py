"""STDIO transport tests.

Spawns a mock MCP server as a subprocess and communicates with it over
stdin/stdout using the SDK's ``stdio_client``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tests.conftest import EXPECTED_TOOL_NAMES

_MOCK_SERVER_SCRIPT = str(Path(__file__).resolve().parent / "mock_stdio_server.py")


@pytest.fixture()
def server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[_MOCK_SERVER_SCRIPT],
    )


async def test_initialize(server_params):
    """Client can connect and initialise over STDIO."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        assert session is not None


async def test_list_tools(server_params):
    """list_tools() returns the expected tools over STDIO."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}
        assert tool_names == EXPECTED_TOOL_NAMES


async def test_call_tool(server_params):
    """A tool call round-trips correctly over STDIO."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("get_entity_names", {})
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert result.content[0].text.startswith("ok:")

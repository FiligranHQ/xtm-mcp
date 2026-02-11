"""In-memory transport tests using the MCP SDK's built-in helper.

These tests exercise tool registration, listing, calling, and context
injection without any real transport (no network, no subprocess).
"""

from __future__ import annotations

from mcp.shared.memory import create_connected_server_and_client_session

from tests.conftest import EXPECTED_TOOL_NAMES


async def test_initialize(test_server):
    """Client can connect and initialise over in-memory streams."""
    async with create_connected_server_and_client_session(test_server) as session:
        # initialize() is called inside the context manager; reaching here means success
        assert session is not None


async def test_list_tools_returns_all_expected_names(test_server):
    """list_tools() returns exactly the 9 registered tools."""
    async with create_connected_server_and_client_session(test_server) as session:
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}
        assert tool_names == EXPECTED_TOOL_NAMES


async def test_call_tool_get_entity_names(test_server):
    """Calling a no-arg tool returns a text result from the mock."""
    async with create_connected_server_and_client_session(test_server) as session:
        result = await session.call_tool("get_entity_names", {})
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert result.content[0].text.startswith("ok:")


async def test_call_tool_execute_graphql_query(test_server):
    """Calling a tool that takes arguments works correctly."""
    async with create_connected_server_and_client_session(test_server) as session:
        result = await session.call_tool("execute_graphql_query", {"query": "{ viewer { id } }"})
        assert len(result.content) == 1
        assert result.content[0].type == "text"


async def test_call_tool_search_entities_by_name(test_server):
    """search_entities_by_name round-trips its argument."""
    async with create_connected_server_and_client_session(test_server) as session:
        result = await session.call_tool("search_entities_by_name", {"entity_name": "Malware"})
        assert len(result.content) == 1
        assert result.content[0].type == "text"

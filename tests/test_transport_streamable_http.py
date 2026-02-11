"""Streamable HTTP transport tests.

Starts a mock MCP server with streamable-http transport on a local port and
connects to it using the SDK's ``streamable_http_client``.
"""

from __future__ import annotations

import asyncio
import socket
from contextlib import suppress

import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from tests.conftest import EXPECTED_TOOL_NAMES, create_test_server


def _free_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


async def _wait_for_server(host: str, port: int, timeout: float = 10.0) -> None:
    """Block until the server is accepting TCP connections."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(0.1)
    raise TimeoutError(f"Server on {host}:{port} did not start within {timeout}s")


@pytest.fixture()
async def streamable_http_server_url():
    """Start a mock streamable-http server in the background and yield its URL."""
    port = _free_port()
    server = create_test_server(host="127.0.0.1", port=port)
    url = f"http://127.0.0.1:{port}/mcp"

    task = asyncio.create_task(server.run_streamable_http_async())
    try:
        await _wait_for_server("127.0.0.1", port)
        yield url
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def test_initialize(streamable_http_server_url):
    """Client can connect and initialise over streamable HTTP."""
    async with (
        streamable_http_client(streamable_http_server_url) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        assert session is not None


async def test_list_tools(streamable_http_server_url):
    """list_tools() returns the expected tools over streamable HTTP."""
    async with (
        streamable_http_client(streamable_http_server_url) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}
        assert tool_names == EXPECTED_TOOL_NAMES


async def test_call_tool(streamable_http_server_url):
    """A tool call round-trips correctly over streamable HTTP."""
    async with (
        streamable_http_client(streamable_http_server_url) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("get_entity_names", {})
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert result.content[0].text.startswith("ok:")

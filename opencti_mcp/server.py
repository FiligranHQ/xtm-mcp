import argparse
import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from functools import partial
from logging import INFO, basicConfig, getLogger
from typing import Any

from dotenv import load_dotenv
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from mcp import types as mcp_types
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from opencti_mcp.tools import (
    execute_graphql_query,
    get_entity_names,
    get_query_fields,
    get_stix_relationships_mapping,
    get_types_definitions,
    list_graphql_types,
    search_entities_by_name,
    validate_graphql_query,
)

logger = getLogger(__name__)


def configure_logging() -> None:
    basicConfig(level=INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenCTI GraphQL MCP server")
    parser.add_argument(
        "--url",
        dest="url",
        default=None,
        help=("OpenCTI base URL (the server will use the /graphql endpoint)"),
    )
    parser.add_argument("--token", dest="token", default=None, help="OpenCTI API token")
    return parser.parse_args()


class ServerContext:
    def __init__(self, client: Client):
        self.client = client


@asynccontextmanager
async def server_lifespan(
    server: Server[ServerContext], url: str, token: str
) -> AsyncIterator[ServerContext]:
    def build_graphql_url(base_url: str) -> str:
        # Normalize base URL and ensure it ends with /graphql
        normalized = base_url.rstrip("/")
        if normalized.endswith("/graphql"):
            return normalized
        return f"{normalized}/graphql"

    headers = {"Authorization": f"Bearer {token}"}
    transport = AIOHTTPTransport(url=build_graphql_url(url), headers=headers)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    try:
        context = ServerContext(client)
        yield context
    finally:
        with suppress(Exception):
            await client.close_async()


async def list_tools_impl(_server: Server[ServerContext]) -> list[Tool]:
    return [
        Tool(
            name="list_graphql_types",
            description="Fetch and return the list of all GraphQL types",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_types_definitions",
            description="Fetch and return the definition of one or more GraphQL types",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_name": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Name(s) of the GraphQL type(s) to fetch.",
                    }
                },
                "required": ["type_name"],
            },
        ),
        Tool(
            name="execute_graphql_query",
            description="Execute a GraphQL query and return the result",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "GraphQL query"}},
                "required": ["query"],
            },
        ),
        Tool(
            name="validate_graphql_query",
            description="Validate a GraphQL query without returning its result.",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "GraphQL query"}},
                "required": ["query"],
            },
        ),
        Tool(
            name="get_stix_relationships_mapping",
            description=(
                "Get all possible STIX relationships between types and their "
                "available relationship types"
            ),
            inputSchema={
                "type": "object",
                "properties": {"type_name": {"type": "string", "description": "Optional filter"}},
            },
        ),
        Tool(
            name="get_query_fields",
            description="Get all field names from the GraphQL Query type",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_entity_names",
            description="Get all unique entity names from STIX relationships mapping",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="search_entities_by_name",
            description="Search for entities by name and intersect with available entity types",
            inputSchema={
                "type": "object",
                "properties": {"entity_name": {"type": "string", "description": "Entity name"}},
                "required": ["entity_name"],
            },
        ),
    ]


async def call_tool_impl(
    _server: Server[ServerContext], name: str, arguments: dict[str, Any]
) -> list[mcp_types.TextContent]:
    try:
        ctx = _server.request_context
        client = ctx.lifespan_context.client
        async with client as session:
            handlers = {
                "list_graphql_types": list_graphql_types.handle,
                "get_types_definitions": get_types_definitions.handle,
                "execute_graphql_query": execute_graphql_query.handle,
                "validate_graphql_query": validate_graphql_query.handle,
                "get_stix_relationships_mapping": get_stix_relationships_mapping.handle,
                "get_query_fields": get_query_fields.handle,
                "get_entity_names": get_entity_names.handle,
                "search_entities_by_name": search_entities_by_name.handle,
            }
            if name not in handlers:
                return [mcp_types.TextContent(type="text", text=f"Unknown tool: {name}")]
            return await handlers[name](session, arguments)
    except Exception as e:  # noqa: BLE001
        return [mcp_types.TextContent(type="text", text=f"Error: {str(e)}")]


async def serve(url: str, token: str) -> None:
    server = Server[ServerContext](
        "opencti-graphql-mcp",
        lifespan=partial(server_lifespan, url=url, token=token),
    )
    server.list_tools()(partial(list_tools_impl, server))
    server.call_tool()(partial(call_tool_impl, server))

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="opencti-graphql-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    configure_logging()
    load_dotenv()
    args = parse_args()

    url: str | None = args.url or os.getenv("OPENCTI_URL")
    token: str | None = args.token or os.getenv("OPENCTI_TOKEN")

    if not url:
        raise SystemExit("OPENCTI_URL is required (via --url or env)")
    if not token:
        raise SystemExit("OPENCTI_TOKEN is required (via --token or env)")

    asyncio.run(serve(url=url, token=token))


if __name__ == "__main__":
    main()

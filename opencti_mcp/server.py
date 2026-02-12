import argparse
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from logging import INFO, basicConfig, getLogger
from typing import Any

from dotenv import load_dotenv
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from mcp import types as mcp_types
from mcp.server.fastmcp import Context, FastMCP

from opencti_mcp.tools import (
    execute_graphql_query as execute_graphql_query_tool,
)
from opencti_mcp.tools import (
    get_entity_names as get_entity_names_tool,
)
from opencti_mcp.tools import (
    get_query_fields as get_query_fields_tool,
)
from opencti_mcp.tools import (
    get_stix_relationships_mapping as get_stix_relationships_mapping_tool,
)
from opencti_mcp.tools import (
    get_types_definitions as get_types_definitions_tool,
)
from opencti_mcp.tools import (
    get_types_definitions_from_schema as get_types_definitions_from_schema_tool,
)
from opencti_mcp.tools import (
    list_graphql_types as list_graphql_types_tool,
)
from opencti_mcp.tools import (
    search_entities_by_name as search_entities_by_name_tool,
)
from opencti_mcp.tools import (
    validate_graphql_query as validate_graphql_query_tool,
)
from opencti_mcp.utils.common import read_opencti_env

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
    parser.add_argument(
        "--transport",
        dest="transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        dest="host",
        default="127.0.0.1",
        help="Host to bind for HTTP-based transports (streamable-http, sse)",
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=8000,
        help="Port to bind for HTTP-based transports (streamable-http, sse)",
    )
    parser.add_argument(
        "--stateless-http",
        dest="stateless_http",
        action="store_true",
        help="Use stateless HTTP mode (streamable-http only)",
    )
    parser.add_argument(
        "--json-response",
        dest="json_response",
        action="store_true",
        help="Return JSON HTTP responses instead of SSE (streamable-http only)",
    )
    return parser.parse_args()


class ServerContext:
    def __init__(self, client: Client):
        self.client = client


def _build_graphql_url(base_url: str) -> str:
    """Normalize base URL and ensure it ends with /graphql."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/graphql"):
        return normalized
    return f"{normalized}/graphql"


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[ServerContext]:
    """Lifespan manager that initializes and cleans up the GraphQL client."""
    url, token = read_opencti_env(strict=True)

    headers = {"Authorization": f"Bearer {token}"}
    transport = AIOHTTPTransport(url=_build_graphql_url(url), headers=headers)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    try:
        context = ServerContext(client)
        yield context
    finally:
        with suppress(Exception):
            await client.close_async()


mcp_server = FastMCP("opencti-graphql-mcp", lifespan=app_lifespan)


async def _with_session(
    ctx: Context,
    handler: Any,
    arguments: dict[str, Any],
) -> list[mcp_types.TextContent]:
    """Helper to run a tool handler with a GraphQL session from the lifespan context."""
    client = ctx.request_context.lifespan_context.client
    async with client as session:
        result: list[mcp_types.TextContent] = await handler(session, arguments)
        return result


@mcp_server.tool()
async def list_graphql_types(
    ctx: Context,
) -> list[mcp_types.TextContent]:
    """Fetch and return the list of all GraphQL types."""
    return await _with_session(ctx, list_graphql_types_tool.handle, {})


@mcp_server.tool()
async def get_types_definitions(
    ctx: Context,
    type_name: str | list[str],
) -> list[mcp_types.TextContent]:
    """Fetch and return the definition of one or more GraphQL types."""
    return await _with_session(ctx, get_types_definitions_tool.handle, {"type_name": type_name})


@mcp_server.tool()
async def get_types_definitions_from_schema(
    ctx: Context,
) -> list[mcp_types.TextContent]:
    """Return all type definitions using /schema (SDL) and local introspection."""
    return await _with_session(
        ctx,
        get_types_definitions_from_schema_tool.handle,
        {},
    )


@mcp_server.tool()
async def execute_graphql_query(
    ctx: Context,
    query: str,
) -> list[mcp_types.TextContent]:
    """Execute a GraphQL query and return the result."""
    return await _with_session(ctx, execute_graphql_query_tool.handle, {"query": query})


@mcp_server.tool()
async def validate_graphql_query(
    ctx: Context,
    query: str,
) -> list[mcp_types.TextContent]:
    """Validate a GraphQL query without returning its result."""
    return await _with_session(ctx, validate_graphql_query_tool.handle, {"query": query})


@mcp_server.tool()
async def get_stix_relationships_mapping(
    ctx: Context,
    type_name: str | None = None,
) -> list[mcp_types.TextContent]:
    """Get all possible STIX relationships between types and their available relationship types."""
    arguments: dict[str, Any] = {}
    if type_name:
        arguments["type_name"] = type_name
    return await _with_session(ctx, get_stix_relationships_mapping_tool.handle, arguments)


@mcp_server.tool()
async def get_query_fields(
    ctx: Context,
) -> list[mcp_types.TextContent]:
    """Get all field names from the GraphQL Query type."""
    return await _with_session(ctx, get_query_fields_tool.handle, {})


@mcp_server.tool()
async def get_entity_names(
    ctx: Context,
) -> list[mcp_types.TextContent]:
    """Get all unique entity names from STIX relationships mapping."""
    return await _with_session(ctx, get_entity_names_tool.handle, {})


@mcp_server.tool()
async def search_entities_by_name(
    ctx: Context,
    entity_name: str,
) -> list[mcp_types.TextContent]:
    """Search for entities by name and intersect with available entity types."""
    return await _with_session(
        ctx,
        search_entities_by_name_tool.handle,
        {"entity_name": entity_name},
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

    # Ensure downstream helpers and tools see the resolved values via environment variables.
    os.environ["OPENCTI_URL"] = url
    os.environ["OPENCTI_TOKEN"] = token

    # Configure transport settings – FastMCP.run() reads from self.settings
    mcp_server.settings.host = args.host
    mcp_server.settings.port = args.port
    mcp_server.settings.stateless_http = args.stateless_http
    mcp_server.settings.json_response = args.json_response

    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()

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
    add_note as add_note_tool,
)
from opencti_mcp.tools import (
    create_external_reference as create_external_reference_tool,
)
from opencti_mcp.tools import (
    create_grouping as create_grouping_tool,
)
from opencti_mcp.tools import (
    create_identity as create_identity_tool,
)
from opencti_mcp.tools import (
    create_label as create_label_tool,
)
from opencti_mcp.tools import (
    create_relationship as create_relationship_tool,
)
from opencti_mcp.tools import (
    create_report as create_report_tool,
)
from opencti_mcp.tools import (
    execute_graphql_query as execute_graphql_query_tool,
)
from opencti_mcp.tools import (
    get_entity_names as get_entity_names_tool,
)
from opencti_mcp.tools import (
    get_license_edition as get_license_edition_tool,
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
    list_identities as list_identities_tool,
)
from opencti_mcp.tools import (
    list_labels as list_labels_tool,
)
from opencti_mcp.tools import (
    list_marking_definitions as list_marking_definitions_tool,
)
from opencti_mcp.tools import (
    list_stix_core_objects as list_stix_core_objects_tool,
)
from opencti_mcp.tools import (
    list_stix_core_relationships as list_stix_core_relationships_tool,
)
from opencti_mcp.tools import (
    read_identity as read_identity_tool,
)
from opencti_mcp.tools import (
    read_label as read_label_tool,
)
from opencti_mcp.tools import (
    read_marking_definition as read_marking_definition_tool,
)
from opencti_mcp.tools import (
    read_stix_core_object as read_stix_core_object_tool,
)
from opencti_mcp.tools import (
    read_stix_core_relationship as read_stix_core_relationship_tool,
)
from opencti_mcp.tools import (
    search_entities_by_name as search_entities_by_name_tool,
)
from opencti_mcp.tools import (
    validate_graphql_query as validate_graphql_query_tool,
)
from opencti_mcp.utils.common import read_opencti_env

logger = getLogger(__name__)
_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


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
    parser.add_argument(
        "--enable-mutations",
        dest="enable_mutations",
        action="store_true",
        help=(
            "Enable write tools (create_report, add_note, create_relationship, "
            "create_identity, create_grouping, create_external_reference, create_label). "
            "Mutations are disabled by default."
        ),
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
async def get_license_edition(
    ctx: Context,
) -> list[mcp_types.TextContent]:
    """Detect whether OpenCTI runs Community Edition (CE) or Enterprise Edition (EE)."""
    return await _with_session(ctx, get_license_edition_tool.handle, {})


@mcp_server.tool()
async def list_identities(
    ctx: Context,
    types: list[str] | None = None,
    search: str | None = None,
    first: int = 50,
    after: str | None = None,
    orderBy: str | None = None,  # noqa: N803
    orderMode: str | None = None,  # noqa: N803
) -> list[mcp_types.TextContent]:
    """List identities (brand, suppliers, subsidiaries) with optional filters."""
    arguments: dict[str, Any] = {"first": first}
    if types is not None:
        arguments["types"] = types
    if search is not None:
        arguments["search"] = search
    if after is not None:
        arguments["after"] = after
    if orderBy is not None:
        arguments["orderBy"] = orderBy
    if orderMode is not None:
        arguments["orderMode"] = orderMode
    return await _with_session(ctx, list_identities_tool.handle, arguments)


@mcp_server.tool()
async def read_identity(
    ctx: Context,
    id: str,  # noqa: A002
) -> list[mcp_types.TextContent]:
    """Read one identity by OpenCTI ID."""
    return await _with_session(ctx, read_identity_tool.handle, {"id": id})


@mcp_server.tool()
async def list_stix_core_objects(
    ctx: Context,
    types: list[str] | None = None,
    search: str | None = None,
    first: int = 50,
    after: str | None = None,
    orderBy: str | None = None,  # noqa: N803
    orderMode: str | None = None,  # noqa: N803
) -> list[mcp_types.TextContent]:
    """List STIX Core Objects across reports, campaigns, threats, TTPs and vulnerabilities."""
    arguments: dict[str, Any] = {"first": first}
    if types is not None:
        arguments["types"] = types
    if search is not None:
        arguments["search"] = search
    if after is not None:
        arguments["after"] = after
    if orderBy is not None:
        arguments["orderBy"] = orderBy
    if orderMode is not None:
        arguments["orderMode"] = orderMode
    return await _with_session(ctx, list_stix_core_objects_tool.handle, arguments)


@mcp_server.tool()
async def read_stix_core_object(
    ctx: Context,
    id: str,  # noqa: A002
) -> list[mcp_types.TextContent]:
    """Read one STIX Core Object by OpenCTI ID."""
    return await _with_session(ctx, read_stix_core_object_tool.handle, {"id": id})


@mcp_server.tool()
async def list_stix_core_relationships(
    ctx: Context,
    from_or_to_ids: list[str] | None = None,
    from_ids: list[str] | None = None,
    to_ids: list[str] | None = None,
    relationship_types: list[str] | None = None,
    search: str | None = None,
    first: int = 100,
    after: str | None = None,
    orderBy: str | None = None,  # noqa: N803
    orderMode: str | None = None,  # noqa: N803
) -> list[mcp_types.TextContent]:
    """List STIX Core Relationships for pivoting and impact explanations."""
    arguments: dict[str, Any] = {"first": first}
    if from_or_to_ids is not None:
        arguments["from_or_to_ids"] = from_or_to_ids
    if from_ids is not None:
        arguments["from_ids"] = from_ids
    if to_ids is not None:
        arguments["to_ids"] = to_ids
    if relationship_types is not None:
        arguments["relationship_types"] = relationship_types
    if search is not None:
        arguments["search"] = search
    if after is not None:
        arguments["after"] = after
    if orderBy is not None:
        arguments["orderBy"] = orderBy
    if orderMode is not None:
        arguments["orderMode"] = orderMode
    return await _with_session(ctx, list_stix_core_relationships_tool.handle, arguments)


@mcp_server.tool()
async def read_stix_core_relationship(
    ctx: Context,
    id: str,  # noqa: A002
) -> list[mcp_types.TextContent]:
    """Read one STIX Core Relationship by OpenCTI ID."""
    return await _with_session(ctx, read_stix_core_relationship_tool.handle, {"id": id})


@mcp_server.tool()
async def list_marking_definitions(
    ctx: Context,
    first: int = 100,
    after: str | None = None,
    orderBy: str | None = None,  # noqa: N803
    orderMode: str | None = None,  # noqa: N803
) -> list[mcp_types.TextContent]:
    """List marking definitions (e.g. TLP) available in the instance."""
    arguments: dict[str, Any] = {"first": first}
    if after is not None:
        arguments["after"] = after
    if orderBy is not None:
        arguments["orderBy"] = orderBy
    if orderMode is not None:
        arguments["orderMode"] = orderMode
    return await _with_session(ctx, list_marking_definitions_tool.handle, arguments)


@mcp_server.tool()
async def read_marking_definition(
    ctx: Context,
    id: str,  # noqa: A002
) -> list[mcp_types.TextContent]:
    """Read one marking definition by OpenCTI ID."""
    return await _with_session(ctx, read_marking_definition_tool.handle, {"id": id})


@mcp_server.tool()
async def list_labels(
    ctx: Context,
    search: str | None = None,
    first: int = 100,
    after: str | None = None,
    orderBy: str | None = None,  # noqa: N803
    orderMode: str | None = None,  # noqa: N803
) -> list[mcp_types.TextContent]:
    """List labels with optional search."""
    arguments: dict[str, Any] = {"first": first}
    if search is not None:
        arguments["search"] = search
    if after is not None:
        arguments["after"] = after
    if orderBy is not None:
        arguments["orderBy"] = orderBy
    if orderMode is not None:
        arguments["orderMode"] = orderMode
    return await _with_session(ctx, list_labels_tool.handle, arguments)


@mcp_server.tool()
async def read_label(
    ctx: Context,
    id: str,  # noqa: A002
) -> list[mcp_types.TextContent]:
    """Read one label by OpenCTI ID."""
    return await _with_session(ctx, read_label_tool.handle, {"id": id})


@mcp_server.tool()
async def create_identity(
    ctx: Context,
    name: str,
    type: str = "Organization",  # noqa: A002
    description: str | None = None,
    contact_information: str | None = None,
    confidence: int = 80,
    object_marking: list[str] | None = None,
    object_label: list[str] | None = None,
    external_references: list[str] | None = None,
    x_opencti_organization_type: str | None = None,
    update: bool = False,
) -> list[mcp_types.TextContent]:
    """Create an identity (organization, individual, system, etc.)."""
    arguments: dict[str, Any] = {
        "name": name,
        "type": type,
        "confidence": confidence,
        "update": update,
    }
    if description is not None:
        arguments["description"] = description
    if contact_information is not None:
        arguments["contact_information"] = contact_information
    if object_marking is not None:
        arguments["object_marking"] = object_marking
    if object_label is not None:
        arguments["object_label"] = object_label
    if external_references is not None:
        arguments["external_references"] = external_references
    if x_opencti_organization_type is not None:
        arguments["x_opencti_organization_type"] = x_opencti_organization_type
    return await _with_session(ctx, create_identity_tool.handle, arguments)


@mcp_server.tool()
async def create_grouping(
    ctx: Context,
    name: str,
    context: str,
    description: str | None = None,
    content: str | None = None,
    objects: list[str] | None = None,
    object_marking: list[str] | None = None,
    object_label: list[str] | None = None,
    external_references: list[str] | None = None,
    confidence: int = 80,
    update: bool = False,
) -> list[mcp_types.TextContent]:
    """Create a grouping to bundle all objects used in a brand pulse."""
    arguments: dict[str, Any] = {
        "name": name,
        "context": context,
        "confidence": confidence,
        "update": update,
    }
    if description is not None:
        arguments["description"] = description
    if content is not None:
        arguments["content"] = content
    if objects is not None:
        arguments["objects"] = objects
    if object_marking is not None:
        arguments["object_marking"] = object_marking
    if object_label is not None:
        arguments["object_label"] = object_label
    if external_references is not None:
        arguments["external_references"] = external_references
    return await _with_session(ctx, create_grouping_tool.handle, arguments)


@mcp_server.tool()
async def create_external_reference(
    ctx: Context,
    source_name: str | None = None,
    url: str | None = None,
    description: str | None = None,
    external_id: str | None = None,
    x_opencti_stix_ids: list[str] | None = None,
    update: bool = False,
) -> list[mcp_types.TextContent]:
    """Create an external reference (vendor advisory, takedown portal, case URL, etc.)."""
    arguments: dict[str, Any] = {"update": update}
    if source_name is not None:
        arguments["source_name"] = source_name
    if url is not None:
        arguments["url"] = url
    if description is not None:
        arguments["description"] = description
    if external_id is not None:
        arguments["external_id"] = external_id
    if x_opencti_stix_ids is not None:
        arguments["x_opencti_stix_ids"] = x_opencti_stix_ids
    return await _with_session(ctx, create_external_reference_tool.handle, arguments)


@mcp_server.tool()
async def create_label(
    ctx: Context,
    value: str,
    color: str | None = None,
    update: bool = False,
) -> list[mcp_types.TextContent]:
    """Create a label for internal taxonomy/tagging."""
    arguments: dict[str, Any] = {
        "value": value,
        "update": update,
    }
    if color is not None:
        arguments["color"] = color
    return await _with_session(ctx, create_label_tool.handle, arguments)


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


@mcp_server.tool()
async def create_report(
    ctx: Context,
    name: str,
    description: str,
    report_types: list[str] | None = None,
    published: str | None = None,
    confidence: int = 80,
    objects: list[str] | None = None,
    labels: list[str] | None = None,
) -> list[mcp_types.TextContent]:
    """Create a report in OpenCTI."""
    arguments: dict[str, Any] = {
        "name": name,
        "description": description,
        "confidence": confidence,
    }
    if report_types is not None:
        arguments["report_types"] = report_types
    if published is not None:
        arguments["published"] = published
    if objects is not None:
        arguments["objects"] = objects
    if labels is not None:
        arguments["labels"] = labels
    return await _with_session(ctx, create_report_tool.handle, arguments)


@mcp_server.tool()
async def add_note(
    ctx: Context,
    content: str,
    objects: list[str],
    attribute_abstract: str | None = None,
    note_types: list[str] | None = None,
    confidence: int = 80,
) -> list[mcp_types.TextContent]:
    """Add a note to one or more entities in OpenCTI."""
    arguments: dict[str, Any] = {
        "content": content,
        "objects": objects,
        "confidence": confidence,
    }
    if attribute_abstract is not None:
        arguments["attribute_abstract"] = attribute_abstract
    if note_types is not None:
        arguments["note_types"] = note_types
    return await _with_session(ctx, add_note_tool.handle, arguments)


@mcp_server.tool()
async def create_relationship(
    ctx: Context,
    fromId: str,  # noqa: N803
    toId: str,  # noqa: N803
    relationship_type: str,
) -> list[mcp_types.TextContent]:
    """Create a relationship between two entities in OpenCTI."""
    return await _with_session(
        ctx,
        create_relationship_tool.handle,
        {
            "fromId": fromId,
            "toId": toId,
            "relationship_type": relationship_type,
        },
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

    mutations_enabled = args.enable_mutations or (
        os.getenv("OPENCTI_ENABLE_MUTATIONS", "").strip().lower() in _TRUE_ENV_VALUES
    )
    os.environ["OPENCTI_ENABLE_MUTATIONS"] = "true" if mutations_enabled else "false"
    if mutations_enabled:
        logger.info("Mutation tools are enabled.")
    else:
        logger.info("Mutation tools are disabled. Use --enable-mutations to enable writes.")

    # Configure transport settings – FastMCP.run() reads from self.settings
    mcp_server.settings.host = args.host
    mcp_server.settings.port = args.port
    mcp_server.settings.stateless_http = args.stateless_http
    mcp_server.settings.json_response = args.json_response

    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()

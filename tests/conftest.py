"""Shared fixtures for MCP transport tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import types as mcp_types
from mcp.server.fastmcp import Context, FastMCP

# ---------------------------------------------------------------------------
# Expected tool names (must match the @mcp_server.tool() registrations in
# opencti_mcp/server.py).
# ---------------------------------------------------------------------------

EXPECTED_TOOL_NAMES: set[str] = {
    "list_graphql_types",
    "get_types_definitions",
    "get_types_definitions_from_schema",
    "execute_graphql_query",
    "validate_graphql_query",
    "get_stix_relationships_mapping",
    "get_query_fields",
    "get_entity_names",
    "get_license_edition",
    "list_identities",
    "read_identity",
    "list_stix_core_objects",
    "read_stix_core_object",
    "list_stix_core_relationships",
    "read_stix_core_relationship",
    "list_marking_definitions",
    "read_marking_definition",
    "list_labels",
    "read_label",
    "search_entities_by_name",
    "create_identity",
    "create_grouping",
    "create_external_reference",
    "create_label",
    "create_report",
    "add_note",
    "create_relationship",
}


# ---------------------------------------------------------------------------
# Mock lifespan & ServerContext
# ---------------------------------------------------------------------------


class _MockServerContext:
    """Drop-in replacement for ``opencti_mcp.server.ServerContext``."""

    def __init__(self, client: Any) -> None:
        self.client = client


def _make_mock_gql_client() -> MagicMock:
    """Return a mock ``gql.Client`` that behaves as an async context manager.

    ``async with client as session`` yields a mock session whose ``.execute``
    returns a canned GraphQL-style response.
    """
    mock_session = AsyncMock()
    mock_session.execute.return_value = {
        "__schema": {"types": [{"name": "Query"}, {"name": "Mutation"}]}
    }

    mock_client = MagicMock()
    # Support `async with client as session:`
    mock_client.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@asynccontextmanager
async def mock_lifespan(_server: FastMCP) -> AsyncIterator[_MockServerContext]:
    """Lifespan that yields a mock ``ServerContext`` – no real OpenCTI needed."""
    yield _MockServerContext(client=_make_mock_gql_client())


# ---------------------------------------------------------------------------
# Test-server factory
# ---------------------------------------------------------------------------


async def _echo_via_context(ctx: Context) -> list[mcp_types.TextContent]:
    """Helper: exercises the lifespan context and mock gql session."""
    client = ctx.request_context.lifespan_context.client
    async with client as session:
        result = await session.execute(None)
    return [mcp_types.TextContent(type="text", text=f"ok:{result}")]


def _register_tools(server: FastMCP) -> None:
    """Register the same tools as the production server, but backed by a
    simple echo handler so we can verify round-trip over every transport.

    Each function is defined at module level (via decorator) so that FastMCP's
    signature introspection sees clean parameter names (no leading ``_``).
    """

    @server.tool(name="list_graphql_types")
    async def list_graphql_types(ctx: Context) -> list[mcp_types.TextContent]:
        """Fetch and return the list of all GraphQL types."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_types_definitions_from_schema")
    async def get_types_definitions_from_schema(ctx: Context) -> list[mcp_types.TextContent]:
        """Return all type definitions using /schema (SDL) and local introspection."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_query_fields")
    async def get_query_fields(ctx: Context) -> list[mcp_types.TextContent]:
        """Get all field names from the GraphQL Query type."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_entity_names")
    async def get_entity_names(ctx: Context) -> list[mcp_types.TextContent]:
        """Get all unique entity names from STIX relationships mapping."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_license_edition")
    async def get_license_edition(ctx: Context) -> list[mcp_types.TextContent]:
        """Detect whether the target OpenCTI is CE or EE."""
        return await _echo_via_context(ctx)

    @server.tool(name="list_identities")
    async def list_identities(
        ctx: Context,
        types: list[str] | None = None,
        search: str | None = None,
        first: int = 50,
        after: str | None = None,
        orderBy: str | None = None,  # noqa: N803
        orderMode: str | None = None,  # noqa: N803
    ) -> list[mcp_types.TextContent]:
        """List identities with optional filters."""
        return await _echo_via_context(ctx)

    @server.tool(name="read_identity")
    async def read_identity(ctx: Context, id: str) -> list[mcp_types.TextContent]:  # noqa: A002
        """Read one identity by ID."""
        return await _echo_via_context(ctx)

    @server.tool(name="list_stix_core_objects")
    async def list_stix_core_objects(
        ctx: Context,
        types: list[str] | None = None,
        search: str | None = None,
        first: int = 50,
        after: str | None = None,
        orderBy: str | None = None,  # noqa: N803
        orderMode: str | None = None,  # noqa: N803
    ) -> list[mcp_types.TextContent]:
        """List STIX core objects with optional filters."""
        return await _echo_via_context(ctx)

    @server.tool(name="read_stix_core_object")
    async def read_stix_core_object(
        ctx: Context,
        id: str,  # noqa: A002
    ) -> list[mcp_types.TextContent]:
        """Read one STIX core object by ID."""
        return await _echo_via_context(ctx)

    @server.tool(name="list_stix_core_relationships")
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
        """List STIX core relationships with optional filters."""
        return await _echo_via_context(ctx)

    @server.tool(name="read_stix_core_relationship")
    async def read_stix_core_relationship(
        ctx: Context,
        id: str,  # noqa: A002
    ) -> list[mcp_types.TextContent]:
        """Read one STIX core relationship by ID."""
        return await _echo_via_context(ctx)

    @server.tool(name="list_marking_definitions")
    async def list_marking_definitions(
        ctx: Context,
        first: int = 100,
        after: str | None = None,
        orderBy: str | None = None,  # noqa: N803
        orderMode: str | None = None,  # noqa: N803
    ) -> list[mcp_types.TextContent]:
        """List marking definitions."""
        return await _echo_via_context(ctx)

    @server.tool(name="read_marking_definition")
    async def read_marking_definition(
        ctx: Context,
        id: str,  # noqa: A002
    ) -> list[mcp_types.TextContent]:
        """Read one marking definition by ID."""
        return await _echo_via_context(ctx)

    @server.tool(name="list_labels")
    async def list_labels(
        ctx: Context,
        search: str | None = None,
        first: int = 100,
        after: str | None = None,
        orderBy: str | None = None,  # noqa: N803
        orderMode: str | None = None,  # noqa: N803
    ) -> list[mcp_types.TextContent]:
        """List labels."""
        return await _echo_via_context(ctx)

    @server.tool(name="read_label")
    async def read_label(ctx: Context, id: str) -> list[mcp_types.TextContent]:  # noqa: A002
        """Read one label by ID."""
        return await _echo_via_context(ctx)

    @server.tool(name="execute_graphql_query")
    async def execute_graphql_query(ctx: Context, query: str) -> list[mcp_types.TextContent]:
        """Execute a GraphQL query and return the result."""
        return await _echo_via_context(ctx)

    @server.tool(name="validate_graphql_query")
    async def validate_graphql_query(ctx: Context, query: str) -> list[mcp_types.TextContent]:
        """Validate a GraphQL query without returning its result."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_types_definitions")
    async def get_types_definitions(
        ctx: Context,
        type_name: str | list[str],
    ) -> list[mcp_types.TextContent]:
        """Fetch and return the definition of one or more GraphQL types."""
        return await _echo_via_context(ctx)

    @server.tool(name="get_stix_relationships_mapping")
    async def get_stix_relationships_mapping(
        ctx: Context,
        type_name: str | None = None,
    ) -> list[mcp_types.TextContent]:
        """Get all possible STIX relationships between types."""
        return await _echo_via_context(ctx)

    @server.tool(name="search_entities_by_name")
    async def search_entities_by_name(
        ctx: Context,
        entity_name: str,
    ) -> list[mcp_types.TextContent]:
        """Search for entities by name and intersect with available entity types."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_report")
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
        return await _echo_via_context(ctx)

    @server.tool(name="add_note")
    async def add_note(
        ctx: Context,
        content: str,
        objects: list[str],
        attribute_abstract: str | None = None,
        note_types: list[str] | None = None,
        confidence: int = 80,
    ) -> list[mcp_types.TextContent]:
        """Add a note to entities in OpenCTI."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_relationship")
    async def create_relationship(
        ctx: Context,
        fromId: str,  # noqa: N803
        toId: str,  # noqa: N803
        relationship_type: str,
    ) -> list[mcp_types.TextContent]:
        """Create a relationship between entities in OpenCTI."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_identity")
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
        """Create an identity."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_grouping")
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
        """Create a grouping."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_external_reference")
    async def create_external_reference(
        ctx: Context,
        source_name: str | None = None,
        url: str | None = None,
        description: str | None = None,
        external_id: str | None = None,
        x_opencti_stix_ids: list[str] | None = None,
        update: bool = False,
    ) -> list[mcp_types.TextContent]:
        """Create an external reference."""
        return await _echo_via_context(ctx)

    @server.tool(name="create_label")
    async def create_label(
        ctx: Context,
        value: str,
        color: str | None = None,
        update: bool = False,
    ) -> list[mcp_types.TextContent]:
        """Create a label."""
        return await _echo_via_context(ctx)


def create_test_server(**kwargs: Any) -> FastMCP:
    """Build a ``FastMCP`` instance with mock lifespan and all registered tools.

    Extra *kwargs* are forwarded to the ``FastMCP`` constructor (e.g.
    ``host``, ``port``).
    """
    server = FastMCP("test-opencti-mcp", lifespan=mock_lifespan, **kwargs)
    _register_tools(server)
    return server


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_server() -> FastMCP:
    """Return a fresh test ``FastMCP`` server for each test."""
    return create_test_server()

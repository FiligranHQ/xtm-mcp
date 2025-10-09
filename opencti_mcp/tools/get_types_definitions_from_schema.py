import json
from typing import Any

from mcp import types as mcp_types

from opencti_mcp.utils.common import read_opencti_env
from opencti_mcp.utils.relationships import fetch_relationships_mapping_gql
from opencti_mcp.utils.schema_parser import (
    SchemaParser,
    build_introspection_from_sdl,
    fetch_schema_sdl,
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Return all type definitions using /schema (SDL) and fetch relationships.

    - Reads OPENCTI_URL and OPENCTI_TOKEN from env, then .env; fails if missing
    - Loads SDL from /schema and builds introspection locally
    - Fetches relationships via /graphql (schemaRelationsTypesMapping)
    """
    opencti_url, token = read_opencti_env(strict=True)
    sdl = fetch_schema_sdl(opencti_url, token)
    introspection_schema = build_introspection_from_sdl(sdl)
    relationships = await fetch_relationships_mapping_gql(session)
    parser = SchemaParser(introspection_schema, relationships)
    all_defs = parser.get_all_type_definitions()
    return [mcp_types.TextContent(type="text", text=json.dumps(all_defs, indent=2))]

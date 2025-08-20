import json
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import SCHEMA_RELATIONS_TYPES_MAPPING


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    result = await session.execute(gql(SCHEMA_RELATIONS_TYPES_MAPPING))
    mappings = result.get("schemaRelationsTypesMapping", [])
    type_name = arguments.get("type_name")

    # Build adjacency of entity -> set(related_entities)
    related: dict[str, set[str]] = {}
    for mapping in mappings:
        key = mapping["key"]
        if "_" not in key:
            continue
        source_type, target_type = key.split("_", 1)
        if source_type == target_type:
            continue
        related.setdefault(source_type, set()).add(target_type)
        related.setdefault(target_type, set()).add(source_type)

    if type_name:
        relationships = sorted(list(related.get(type_name, set())))
        response: dict[str, Any] = {
            "filtered_type": type_name,
            "relationships_mapping": relationships,
        }
    else:
        # No filter provided: return the full mapping as a dict[str, list[str]]
        full_mapping = {k: sorted(list(v)) for k, v in sorted(related.items())}
        response = {"relationships_mapping": full_mapping}

    return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]

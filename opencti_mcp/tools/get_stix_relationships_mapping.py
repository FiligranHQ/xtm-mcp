import json
from typing import Any

from mcp import types as mcp_types

from opencti_mcp.utils.relationships import (
    build_related_adjacency,
    fetch_relationships_mapping_gql,
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    mappings = await fetch_relationships_mapping_gql(session)
    type_name = arguments.get("type_name")

    # Build adjacency of entity -> set(related_entities)
    related = build_related_adjacency(mappings)

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

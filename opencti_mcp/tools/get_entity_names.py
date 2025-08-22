import json
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import SCHEMA_RELATIONS_TYPES_MAPPING


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    result = await session.execute(gql(SCHEMA_RELATIONS_TYPES_MAPPING))
    mappings = result.get("schemaRelationsTypesMapping", [])

    entity_names: set[str] = set()
    for mapping in mappings:
        key = mapping["key"]
        if "_" in key:
            from_entity, to_entity = key.split("_", 1)
            entity_names.add(from_entity)
            entity_names.add(to_entity)

    entity_names_list = sorted(list(entity_names))
    response = {"entity_names": entity_names_list, "count": len(entity_names_list)}
    return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]

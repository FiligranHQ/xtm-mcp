import json
from typing import Any

from gql import Client, gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import SCHEMA_RELATIONS_TYPES_MAPPING, SEARCH_ENTITIES_BY_NAME


async def handle(session: Client, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    entity_name = arguments.get("entity_name", "").strip()
    if not entity_name:
        return [
            mcp_types.TextContent(
                type="text",
                text="Error: entity_name is required and cannot be empty",
            )
        ]

    search_result = await session.execute(
        gql(SEARCH_ENTITIES_BY_NAME), variable_values={"term": entity_name}
    )

    entity_names_result = await session.execute(gql(SCHEMA_RELATIONS_TYPES_MAPPING))

    found_entity_types: set[str] = set()
    edges = search_result.get("stixCoreObjects", {}).get("edges", [])
    for edge in edges:
        entity_type = edge.get("node", {}).get("entity_type")
        if entity_type:
            found_entity_types.add(entity_type)

    available_entity_types: set[str] = set()
    mappings = entity_names_result.get("schemaRelationsTypesMapping", [])
    for mapping in mappings:
        key = mapping["key"]
        if "_" in key:
            from_entity, to_entity = key.split("_", 1)
            available_entity_types.add(from_entity)
            available_entity_types.add(to_entity)

    intersection = sorted(list(found_entity_types.intersection(available_entity_types)))
    return [mcp_types.TextContent(type="text", text=json.dumps(intersection, indent=2))]



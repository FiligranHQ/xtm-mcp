import json
from logging import getLogger
from typing import Any

from gql import Client, gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import INTROSPECTION_FULL

logger = getLogger(__name__)


async def handle(session: Client, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle get_types_definition tool.

    Accepts a single type name (string) or a JSON array/stringified array of type names,
    and returns simplified field definitions for all provided types.
    """
    logger.info("Executing get_types_definition")

    type_names = arguments.get("type_name")
    if not type_names:
        return [mcp_types.TextContent(type="text", text="Error: type_name is required")]

    # Check if it's a JSON string and parse it
    if isinstance(type_names, str):
        try:
            parsed = json.loads(type_names)
            type_names = parsed if isinstance(parsed, list) else [type_names]
        except json.JSONDecodeError:
            # Not JSON, treat as single string
            type_names = [type_names]

    if not isinstance(type_names, list):
        return [
            mcp_types.TextContent(
                type="text",
                text="Error: type_name must be a string or array of strings",
            )
        ]

    result = await session.execute(gql(INTROSPECTION_FULL))
    all_types = result["__schema"]["types"]

    simplified_output: list[dict[str, list[dict[str, str | None]]]] = []

    for type_name in type_names:
        type_def = next((t for t in all_types if t["name"] == type_name), None)
        if type_def and type_def.get("fields"):
            # Extract field names and their type information
            fields_info: list[dict[str, str | None]] = []
            for field in type_def["fields"]:
                field_type = field["type"]
                # Handle nested types (like NON_NULL, LIST)
                while field_type.get("ofType"):
                    field_type = field_type["ofType"]

                fields_info.append(
                    {
                        "name": field["name"],
                        "type": field_type.get("name"),
                        "kind": field_type.get("kind"),
                    }
                )
            simplified_output.append({type_name: fields_info})
        else:
            simplified_output.append({type_name: []})

    return [mcp_types.TextContent(type="text", text=json.dumps(simplified_output, indent=2))]

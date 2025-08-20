import json
from typing import Any

from gql import Client, gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import QUERY_FIELDS


async def handle(session: Client, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    result = await session.execute(gql(QUERY_FIELDS))
    query_type = result.get("__type")
    if not query_type or not query_type.get("fields"):
        return [
            mcp_types.TextContent(
                type="text",
                text="Error: Query type not found or has no fields",
            )
        ]

    fields_info: list[dict[str, Any]] = []
    for field in query_type["fields"]:
        field_info = {"name": field["name"], "args": []}
        for arg in field.get("args", []):
            arg_type = arg["type"]
            while arg_type.get("ofType"):
                arg_type = arg_type["ofType"]
            field_info["args"].append({"name": arg["name"], "type": arg_type.get("name")})
        fields_info.append(field_info)

    fields_info.sort(key=lambda x: str(x["name"]))
    response = {"query_fields": fields_info}
    return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]



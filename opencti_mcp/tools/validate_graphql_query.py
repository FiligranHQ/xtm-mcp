import json
from typing import Any

from gql import gql
from mcp import types as mcp_types


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not isinstance(arguments, dict):
        return [
            mcp_types.TextContent(
                type="text",
                text=(f"Error: arguments must be a dictionary, got {type(arguments)}"),
            )
        ]

    query_string = arguments.get("query")
    if not query_string:
        return [
            mcp_types.TextContent(
                type="text",
                text="Error: query parameter is missing or empty",
            )
        ]

    try:
        if not query_string.strip().startswith("query"):
            query_string = f"query {query_string}"
        await session.execute(gql(query_string))
        return [
            mcp_types.TextContent(
                type="text",
                text=json.dumps({"success": True, "error": ""}, indent=2),
            )
        ]
    except Exception as e:  # noqa: BLE001
        return [
            mcp_types.TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]

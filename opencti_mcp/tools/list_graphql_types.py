import json
from typing import Any

from gql import Client, gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import INTROSPECTION_TYPES


async def handle(session: Client, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    result = await session.execute(gql(INTROSPECTION_TYPES))
    types = [t["name"] for t in result["__schema"]["types"]]
    return [mcp_types.TextContent(type="text", text=json.dumps(types, indent=2))]



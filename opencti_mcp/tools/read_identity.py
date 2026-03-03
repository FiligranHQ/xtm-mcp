from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import READ_IDENTITY_QUERY
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    success_response,
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    identity_id, id_error = normalize_non_empty_string(arguments.get("id"), "id", required=True)
    if id_error:
        return error_response(id_error)
    assert identity_id is not None

    try:
        result = await session.execute(
            gql(READ_IDENTITY_QUERY),
            variable_values={"id": identity_id},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("identity", {}))

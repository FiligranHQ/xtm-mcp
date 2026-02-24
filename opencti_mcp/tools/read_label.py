from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import READ_LABEL_QUERY
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

    label_id, label_id_error = normalize_non_empty_string(arguments.get("id"), "id", required=True)
    if label_id_error:
        return error_response(label_id_error)
    assert label_id is not None

    try:
        result = await session.execute(gql(READ_LABEL_QUERY), variable_values={"id": label_id})
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("label", {}))

from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import READ_STIX_CORE_OBJECT_QUERY
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

    object_id, object_id_error = normalize_non_empty_string(
        arguments.get("id"),
        "id",
        required=True,
    )
    if object_id_error:
        return error_response(object_id_error)
    assert object_id is not None

    try:
        result = await session.execute(
            gql(READ_STIX_CORE_OBJECT_QUERY),
            variable_values={"id": object_id},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("stixCoreObject", {}))

from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import LIST_IDENTITIES_QUERY
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_first,
    normalize_non_empty_string,
    normalize_string_list,
    success_response,
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    types_value, types_error = normalize_string_list(arguments.get("types"), "types")
    if types_error:
        return error_response(types_error)

    search, search_error = normalize_non_empty_string(arguments.get("search"), "search")
    if search_error:
        return error_response(search_error)

    first, first_error = normalize_first(arguments.get("first"), default=50)
    if first_error:
        return error_response(first_error)

    after, after_error = normalize_non_empty_string(arguments.get("after"), "after")
    if after_error:
        return error_response(after_error)

    order_by, order_by_error = normalize_non_empty_string(arguments.get("orderBy"), "orderBy")
    if order_by_error:
        return error_response(order_by_error)

    order_mode, order_mode_error = normalize_non_empty_string(
        arguments.get("orderMode"), "orderMode"
    )
    if order_mode_error:
        return error_response(order_mode_error)

    variables = {
        "types": types_value,
        "search": search,
        "first": first,
        "after": after,
        "orderBy": order_by,
        "orderMode": order_mode,
    }

    try:
        result = await session.execute(gql(LIST_IDENTITIES_QUERY), variable_values=variables)
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("identities", {}))

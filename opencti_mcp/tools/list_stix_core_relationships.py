from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import LIST_STIX_CORE_RELATIONSHIPS_QUERY
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_first,
    normalize_non_empty_string,
    normalize_string_list,
    success_response,
)


def _normalize_list_or_string(value: Any, field_name: str) -> tuple[list[str] | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None, f"{field_name} cannot be an empty string"
        return [cleaned], None
    return normalize_string_list(value, field_name)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    from_or_to_id, from_or_to_id_error = _normalize_list_or_string(
        arguments.get("from_or_to_ids"),
        "from_or_to_ids",
    )
    if from_or_to_id_error:
        return error_response(from_or_to_id_error)

    from_id, from_id_error = _normalize_list_or_string(arguments.get("from_ids"), "from_ids")
    if from_id_error:
        return error_response(from_id_error)

    to_id, to_id_error = _normalize_list_or_string(arguments.get("to_ids"), "to_ids")
    if to_id_error:
        return error_response(to_id_error)

    relationship_type, relationship_type_error = _normalize_list_or_string(
        arguments.get("relationship_types"),
        "relationship_types",
    )
    if relationship_type_error:
        return error_response(relationship_type_error)

    search, search_error = normalize_non_empty_string(arguments.get("search"), "search")
    if search_error:
        return error_response(search_error)

    first, first_error = normalize_first(arguments.get("first"), default=100)
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
        "fromOrToId": from_or_to_id,
        "fromId": from_id,
        "toId": to_id,
        "relationship_type": relationship_type,
        "search": search,
        "first": first,
        "after": after,
        "orderBy": order_by,
        "orderMode": order_mode,
    }

    try:
        result = await session.execute(
            gql(LIST_STIX_CORE_RELATIONSHIPS_QUERY),
            variable_values=variables,
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("stixCoreRelationships", {}))

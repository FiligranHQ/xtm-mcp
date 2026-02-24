import re
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    success_response,
)

_OPERATION_PREFIX_PATTERN = re.compile(r"^(query|mutation|subscription)\b", re.IGNORECASE)


def _normalize_graphql_operation(query_string: str) -> str:
    normalized = query_string.strip()
    if _OPERATION_PREFIX_PATTERN.match(normalized):
        return normalized
    return f"query {normalized}"


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    query_string, query_error = normalize_non_empty_string(
        arguments.get("query"),
        "query",
        required=True,
    )
    if query_error:
        return error_response(query_error)
    assert query_string is not None

    try:
        result = await session.execute(gql(_normalize_graphql_operation(query_string)))
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result)

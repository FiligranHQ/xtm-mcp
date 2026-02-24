import re
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_first,
    normalize_non_empty_string,
    success_response,
)

_ENUM_TOKEN_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CASE_RFI_LIST_ROOTS = (
    ("caseRfis", "pirId"),
    ("caseRfis", "casePirId"),
    ("casesRfis", "pirId"),
    ("casesRfis", "casePirId"),
    ("casesRfi", "pirId"),
    ("casesRfi", "casePirId"),
    ("rfis", None),
)


def _normalize_enum_token(value: Any, field_name: str) -> tuple[str | None, str | None]:
    normalized, normalize_error = normalize_non_empty_string(value, field_name)
    if normalize_error:
        return None, normalize_error
    if normalized is None:
        return None, None
    if not _ENUM_TOKEN_PATTERN.fullmatch(normalized):
        return None, (
            f"{field_name} must be a valid GraphQL enum token "
            "(letters, numbers and underscores only)"
        )
    return normalized, None


def _build_list_query(
    root_field: str,
    pir_arg_name: str | None,
    include_pir_filter: bool,
    order_by: str | None = None,
    order_mode: str | None = None,
) -> str:
    variable_declarations = [
        "$search: String",
        "$first: Int",
        "$after: ID",
    ]
    args = [
        "search: $search",
        "first: $first",
        "after: $after",
    ]

    if include_pir_filter and pir_arg_name:
        variable_declarations.append("$pirId: String")
        args.append(f"{pir_arg_name}: $pirId")

    if order_by:
        args.append(f"orderBy: {order_by}")
    if order_mode:
        args.append(f"orderMode: {order_mode}")

    variables_block = ", ".join(variable_declarations)
    args_block = "\n    ".join(args)
    return f"""
query ListCaseRfis({variables_block}) {{
  result: {root_field}(
    {args_block}
  ) {{
    edges {{
      node {{
        id
        name
        description
      }}
    }}
    pageInfo {{
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }}
  }}
}}
"""


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    search, search_error = normalize_non_empty_string(arguments.get("search"), "search")
    if search_error:
        return error_response(search_error)

    first, first_error = normalize_first(arguments.get("first"), default=50)
    if first_error:
        return error_response(first_error)
    assert first is not None

    after, after_error = normalize_non_empty_string(arguments.get("after"), "after")
    if after_error:
        return error_response(after_error)

    pir_id, pir_id_error = normalize_non_empty_string(arguments.get("pir_id"), "pir_id")
    if pir_id_error:
        return error_response(pir_id_error)

    order_by, order_by_error = _normalize_enum_token(arguments.get("orderBy"), "orderBy")
    if order_by_error:
        return error_response(order_by_error)

    order_mode, order_mode_error = _normalize_enum_token(arguments.get("orderMode"), "orderMode")
    if order_mode_error:
        return error_response(order_mode_error)

    base_variables: dict[str, Any] = {
        "search": search,
        "first": first,
        "after": after,
    }

    errors: list[str] = []
    include_ordering_attempts = [True, False] if (order_by or order_mode) else [False]
    include_pir_attempts = [True, False] if pir_id else [False]

    for root_field, pir_arg_name in _CASE_RFI_LIST_ROOTS:
        for include_pir_filter in include_pir_attempts:
            if include_pir_filter and not pir_arg_name:
                continue
            for include_ordering in include_ordering_attempts:
                query = _build_list_query(
                    root_field=root_field,
                    pir_arg_name=pir_arg_name,
                    include_pir_filter=include_pir_filter,
                    order_by=order_by if include_ordering else None,
                    order_mode=order_mode if include_ordering else None,
                )
                variables = base_variables.copy()
                if include_pir_filter:
                    variables["pirId"] = pir_id
                try:
                    result = await session.execute(gql(query), variable_values=variables)
                    return success_response(result.get("result", {}))
                except Exception as error:  # noqa: BLE001
                    errors.append(str(error))

    last_error = errors[-1] if errors else "unknown schema mismatch"
    return error_response(
        "Unable to list case RFIs with the available GraphQL schema variants. "
        f"Last error: {last_error}"
    )

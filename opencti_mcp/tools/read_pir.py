from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    success_response,
)

_PIR_READ_ROOT_FIELDS = ("casePir", "pir")


def _build_read_query(root_field: str) -> str:
    return f"""
query ReadPir($id: String!) {{
  result: {root_field}(id: $id) {{
    id
    name
    description
  }}
}}
"""


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    pir_id, pir_id_error = normalize_non_empty_string(arguments.get("id"), "id", required=True)
    if pir_id_error:
        return error_response(pir_id_error)
    assert pir_id is not None

    errors: list[str] = []
    variables = {"id": pir_id}
    for root_field in _PIR_READ_ROOT_FIELDS:
        try:
            result = await session.execute(
                gql(_build_read_query(root_field)),
                variable_values=variables,
            )
            return success_response(result.get("result"))
        except Exception as error:  # noqa: BLE001
            errors.append(str(error))

    last_error = errors[-1] if errors else "unknown schema mismatch"
    return error_response(
        "Unable to read PIR with the available GraphQL schema variants. "
        f"Last error: {last_error}"
    )

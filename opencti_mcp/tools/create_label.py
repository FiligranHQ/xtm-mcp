from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_LABEL_MUTATION
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    success_response,
)
from opencti_mcp.utils.mutations import mutations_enabled

_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return error_response(_MUTATIONS_DISABLED_MESSAGE)

    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    value, value_error = normalize_non_empty_string(arguments.get("value"), "value", required=True)
    if value_error:
        return error_response(value_error)
    assert value is not None

    color, color_error = normalize_non_empty_string(arguments.get("color"), "color")
    if color_error:
        return error_response(color_error)

    update = arguments.get("update", False)
    if not isinstance(update, bool):
        return error_response("update must be a boolean")

    input_payload: dict[str, Any] = {
        "value": value,
        "update": update,
    }
    if color:
        input_payload["color"] = color

    try:
        result = await session.execute(
            gql(CREATE_LABEL_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("labelAdd", {}))

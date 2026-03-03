from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_RELATIONSHIP_MUTATION
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

    from_id, from_id_error = normalize_non_empty_string(
        arguments.get("fromId"),
        "fromId",
        required=True,
    )
    if from_id_error:
        return error_response(from_id_error)
    assert from_id is not None

    to_id, to_id_error = normalize_non_empty_string(
        arguments.get("toId"),
        "toId",
        required=True,
    )
    if to_id_error:
        return error_response(to_id_error)
    assert to_id is not None

    relationship_type, relationship_type_error = normalize_non_empty_string(
        arguments.get("relationship_type"),
        "relationship_type",
        required=True,
    )
    if relationship_type_error:
        return error_response(relationship_type_error)
    assert relationship_type is not None

    input_payload = {
        "fromId": from_id,
        "toId": to_id,
        "relationship_type": relationship_type,
    }

    try:
        result = await session.execute(
            gql(CREATE_RELATIONSHIP_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    relationship_data = result.get("stixCoreRelationshipAdd", {})
    return success_response(relationship_data)

import json
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_RELATIONSHIP_MUTATION
from opencti_mcp.utils.mutations import mutations_enabled

_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)


def _error_response(message: str) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": message}, indent=2),
        )
    ]


def _success_response(data: Any) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": True, "data": data}, indent=2),
        )
    ]


def _normalize_required_string(value: Any, field_name: str) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, f"{field_name} is required and must be a non-empty string"
    return value.strip(), None


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return _error_response(_MUTATIONS_DISABLED_MESSAGE)

    if not isinstance(arguments, dict):
        return _error_response(f"arguments must be a dictionary, got {type(arguments)}")

    from_id, from_id_error = _normalize_required_string(arguments.get("fromId"), "fromId")
    if from_id_error:
        return _error_response(from_id_error)

    to_id, to_id_error = _normalize_required_string(arguments.get("toId"), "toId")
    if to_id_error:
        return _error_response(to_id_error)

    relationship_type, relationship_type_error = _normalize_required_string(
        arguments.get("relationship_type"), "relationship_type"
    )
    if relationship_type_error:
        return _error_response(relationship_type_error)

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
        return _error_response(str(error))

    relationship_data = result.get("stixCoreRelationshipAdd", {})
    return _success_response(relationship_data)

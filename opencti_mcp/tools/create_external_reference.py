from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_EXTERNAL_REFERENCE_MUTATION
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    normalize_string_list,
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

    source_name, source_name_error = normalize_non_empty_string(
        arguments.get("source_name"), "source_name"
    )
    if source_name_error:
        return error_response(source_name_error)

    url, url_error = normalize_non_empty_string(arguments.get("url"), "url")
    if url_error:
        return error_response(url_error)

    if not source_name and not url:
        return error_response("source_name or url is required")

    description, description_error = normalize_non_empty_string(
        arguments.get("description"), "description"
    )
    if description_error:
        return error_response(description_error)

    external_id, external_id_error = normalize_non_empty_string(
        arguments.get("external_id"),
        "external_id",
    )
    if external_id_error:
        return error_response(external_id_error)

    x_opencti_stix_ids, x_opencti_stix_ids_error = normalize_string_list(
        arguments.get("x_opencti_stix_ids"),
        "x_opencti_stix_ids",
    )
    if x_opencti_stix_ids_error:
        return error_response(x_opencti_stix_ids_error)

    update = arguments.get("update", False)
    if not isinstance(update, bool):
        return error_response("update must be a boolean")

    input_payload: dict[str, Any] = {
        "update": update,
    }
    if source_name:
        input_payload["source_name"] = source_name
    if url:
        input_payload["url"] = url
    if description:
        input_payload["description"] = description
    if external_id:
        input_payload["external_id"] = external_id
    if x_opencti_stix_ids:
        input_payload["x_opencti_stix_ids"] = x_opencti_stix_ids

    try:
        result = await session.execute(
            gql(CREATE_EXTERNAL_REFERENCE_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("externalReferenceAdd", {}))

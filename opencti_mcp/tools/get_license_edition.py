from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import (
    GET_LICENSE_EDITION_QUERY,
    GET_LICENSE_EDITION_QUERY_CAMEL,
)
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    success_response,
)


def _extract_settings_value(settings: dict[str, Any]) -> tuple[str, Any]:
    if "enterprise_edition" in settings:
        return "enterprise_edition", settings.get("enterprise_edition")
    if "enterpriseEdition" in settings:
        return "enterpriseEdition", settings.get("enterpriseEdition")
    return "unknown", None


def _edition_from_value(value: Any) -> str:
    if value in (None, "", False, 0):
        return "CE"
    return "EE"


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    errors: list[str] = []
    for query in (GET_LICENSE_EDITION_QUERY, GET_LICENSE_EDITION_QUERY_CAMEL):
        try:
            result = await session.execute(gql(query))
            settings = result.get("settings")
            if not isinstance(settings, dict):
                return error_response("Unable to read settings from OpenCTI response")

            source_field, raw_value = _extract_settings_value(settings)
            if source_field == "unknown":
                return error_response(
                    "Unable to determine license edition: enterprise edition field not found"
                )

            return success_response(
                {
                    "edition": _edition_from_value(raw_value),
                    "source_field": source_field,
                    "raw_value": raw_value,
                }
            )
        except Exception as error:  # noqa: BLE001
            errors.append(str(error))

    return error_response(
        "Unable to determine license edition from OpenCTI settings. "
        f"Errors: {' | '.join(errors)}"
    )

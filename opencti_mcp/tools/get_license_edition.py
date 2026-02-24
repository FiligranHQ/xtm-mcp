import json
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import (
    GET_LICENSE_EDITION_QUERY,
    GET_LICENSE_EDITION_QUERY_CAMEL,
)


def _error_response(message: str) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": message}, indent=2),
        )
    ]


def _success_response(data: dict[str, Any]) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": True, "data": data}, indent=2),
        )
    ]


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
    if not isinstance(arguments, dict):
        return _error_response(f"arguments must be a dictionary, got {type(arguments)}")

    errors: list[str] = []
    for query in (GET_LICENSE_EDITION_QUERY, GET_LICENSE_EDITION_QUERY_CAMEL):
        try:
            result = await session.execute(gql(query))
            settings = result.get("settings")
            if not isinstance(settings, dict):
                return _error_response("Unable to read settings from OpenCTI response")

            source_field, raw_value = _extract_settings_value(settings)
            if source_field == "unknown":
                return _error_response(
                    "Unable to determine license edition: enterprise edition field not found"
                )

            return _success_response(
                {
                    "edition": _edition_from_value(raw_value),
                    "source_field": source_field,
                    "raw_value": raw_value,
                }
            )
        except Exception as error:  # noqa: BLE001
            errors.append(str(error))

    return _error_response(
        "Unable to determine license edition from OpenCTI settings. "
        f"Errors: {' | '.join(errors)}"
    )

from typing import Any

from gql import gql
from mcp import types as mcp_types

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

_CREATE_PIR_MUTATION = """
mutation CreatePir($input: PirAddInput!) {
  pirAdd(input: $input) {
    id
    name
    description
  }
}
"""
_ALLOWED_PIR_TYPES = {"THREAT_LANDSCAPE", "THREAT_ORIGIN", "THREAT_CUSTOM"}
_ALLOWED_FILTER_MODES = {"and", "or"}


def _default_filter_group() -> dict[str, Any]:
    return {
        "mode": "and",
        "filters": [],
        "filterGroups": [],
    }


def _normalize_positive_int(value: Any, field_name: str, default: int) -> tuple[int | None, str | None]:
    if value is None:
        return default, None
    if isinstance(value, bool) or not isinstance(value, int):
        return None, f"{field_name} must be a positive integer"
    if value < 1:
        return None, f"{field_name} must be a positive integer"
    return value, None


def _normalize_filter(value: Any, field_name: str) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(value, dict):
        return None, f"{field_name} must be an object"

    key, key_error = normalize_string_list(value.get("key"), f"{field_name}.key", required=True)
    if key_error:
        return None, key_error
    assert key is not None

    values, values_error = normalize_string_list(
        value.get("values"),
        f"{field_name}.values",
        required=True,
    )
    if values_error:
        return None, values_error
    assert values is not None

    normalized_filter: dict[str, Any] = {
        "key": key,
        "values": values,
    }

    operator, operator_error = normalize_non_empty_string(value.get("operator"), f"{field_name}.operator")
    if operator_error:
        return None, operator_error
    if operator:
        normalized_filter["operator"] = operator

    mode, mode_error = normalize_non_empty_string(value.get("mode"), f"{field_name}.mode")
    if mode_error:
        return None, mode_error
    if mode:
        if mode not in _ALLOWED_FILTER_MODES:
            return None, f"{field_name}.mode must be one of: {', '.join(sorted(_ALLOWED_FILTER_MODES))}"
        normalized_filter["mode"] = mode

    return normalized_filter, None


def _normalize_filter_group(
    value: Any,
    field_name: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if value is None:
        return _default_filter_group(), None
    if not isinstance(value, dict):
        return None, f"{field_name} must be an object"

    mode, mode_error = normalize_non_empty_string(value.get("mode"), f"{field_name}.mode", required=True)
    if mode_error:
        return None, mode_error
    assert mode is not None
    if mode not in _ALLOWED_FILTER_MODES:
        return None, f"{field_name}.mode must be one of: {', '.join(sorted(_ALLOWED_FILTER_MODES))}"

    filters_raw = value.get("filters", [])
    if not isinstance(filters_raw, list):
        return None, f"{field_name}.filters must be a list"
    filters: list[dict[str, Any]] = []
    for index, filter_value in enumerate(filters_raw):
        normalized_filter, filter_error = _normalize_filter(
            filter_value,
            f"{field_name}.filters[{index}]",
        )
        if filter_error:
            return None, filter_error
        assert normalized_filter is not None
        filters.append(normalized_filter)

    filter_groups_raw = value.get("filterGroups", [])
    if not isinstance(filter_groups_raw, list):
        return None, f"{field_name}.filterGroups must be a list"
    filter_groups: list[dict[str, Any]] = []
    for index, group_value in enumerate(filter_groups_raw):
        normalized_group, group_error = _normalize_filter_group(
            group_value,
            f"{field_name}.filterGroups[{index}]",
        )
        if group_error:
            return None, group_error
        assert normalized_group is not None
        filter_groups.append(normalized_group)

    return {
        "mode": mode,
        "filters": filters,
        "filterGroups": filter_groups,
    }, None


def _normalize_pir_criteria(value: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
    if value is None:
        return [{"weight": 1, "filters": _default_filter_group()}], None
    if not isinstance(value, list):
        return None, "pir_criteria must be a list of objects"
    if not value:
        return None, "pir_criteria cannot be empty"

    criteria: list[dict[str, Any]] = []
    for index, criterion in enumerate(value):
        if not isinstance(criterion, dict):
            return None, f"pir_criteria[{index}] must be an object"

        weight, weight_error = _normalize_positive_int(
            criterion.get("weight"),
            f"pir_criteria[{index}].weight",
            default=1,
        )
        if weight_error:
            return None, weight_error
        assert weight is not None

        filters, filters_error = _normalize_filter_group(
            criterion.get("filters"),
            f"pir_criteria[{index}].filters",
        )
        if filters_error:
            return None, filters_error
        assert filters is not None

        criteria.append(
            {
                "weight": weight,
                "filters": filters,
            }
        )

    return criteria, None


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return error_response(_MUTATIONS_DISABLED_MESSAGE)

    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    name, name_error = normalize_non_empty_string(arguments.get("name"), "name", required=True)
    if name_error:
        return error_response(name_error)
    assert name is not None

    description, description_error = normalize_non_empty_string(
        arguments.get("description"),
        "description",
    )
    if description_error:
        return error_response(description_error)

    pir_type, pir_type_error = normalize_non_empty_string(arguments.get("pir_type"), "pir_type")
    if pir_type_error:
        return error_response(pir_type_error)
    if pir_type is None:
        pir_type = "THREAT_CUSTOM"
    if pir_type not in _ALLOWED_PIR_TYPES:
        return error_response(
            f"pir_type must be one of: {', '.join(sorted(_ALLOWED_PIR_TYPES))}"
        )

    pir_rescan_days, pir_rescan_days_error = _normalize_positive_int(
        arguments.get("pir_rescan_days"),
        "pir_rescan_days",
        default=30,
    )
    if pir_rescan_days_error:
        return error_response(pir_rescan_days_error)
    assert pir_rescan_days is not None

    pir_filters, pir_filters_error = _normalize_filter_group(
        arguments.get("pir_filters"),
        "pir_filters",
    )
    if pir_filters_error:
        return error_response(pir_filters_error)
    assert pir_filters is not None

    pir_criteria, pir_criteria_error = _normalize_pir_criteria(arguments.get("pir_criteria"))
    if pir_criteria_error:
        return error_response(pir_criteria_error)
    assert pir_criteria is not None

    input_payload: dict[str, Any] = {
        "name": name,
        "pir_type": pir_type,
        "pir_rescan_days": pir_rescan_days,
        "pir_filters": pir_filters,
        "pir_criteria": pir_criteria,
    }
    if description:
        input_payload["description"] = description

    try:
        result = await session.execute(
            gql(_CREATE_PIR_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("pirAdd", {}))

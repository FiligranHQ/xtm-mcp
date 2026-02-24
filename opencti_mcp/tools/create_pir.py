from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_confidence,
    normalize_non_empty_string,
    normalize_string_list,
    success_response,
)
from opencti_mcp.utils.mutations import mutations_enabled

_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)

_CREATE_PIR_MUTATIONS = (
    ("casePirAdd", "CasePirAddInput!"),
    ("pirAdd", "PirAddInput!"),
    ("casePirAdd", "PirAddInput!"),
    ("pirAdd", "CasePirAddInput!"),
)


def _build_create_mutation(mutation_name: str, input_type: str) -> str:
    return f"""
mutation CreatePir($input: {input_type}) {{
  result: {mutation_name}(input: $input) {{
    id
    name
    description
  }}
}}
"""


def _payload_candidates(base_payload: dict[str, Any], minimal_payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [base_payload]
    if minimal_payload != base_payload:
        candidates.append(minimal_payload)
    return candidates


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

    content, content_error = normalize_non_empty_string(arguments.get("content"), "content")
    if content_error:
        return error_response(content_error)

    priority, priority_error = normalize_non_empty_string(arguments.get("priority"), "priority")
    if priority_error:
        return error_response(priority_error)

    severity, severity_error = normalize_non_empty_string(arguments.get("severity"), "severity")
    if severity_error:
        return error_response(severity_error)

    confidence, confidence_error = normalize_confidence(arguments.get("confidence"), default=80)
    if confidence_error:
        return error_response(confidence_error)
    assert confidence is not None

    object_marking, object_marking_error = normalize_string_list(
        arguments.get("object_marking"),
        "object_marking",
    )
    if object_marking_error:
        return error_response(object_marking_error)

    object_label, object_label_error = normalize_string_list(
        arguments.get("object_label"),
        "object_label",
    )
    if object_label_error:
        return error_response(object_label_error)

    external_references, external_references_error = normalize_string_list(
        arguments.get("external_references"),
        "external_references",
    )
    if external_references_error:
        return error_response(external_references_error)

    objects, objects_error = normalize_string_list(arguments.get("objects"), "objects")
    if objects_error:
        return error_response(objects_error)

    update = arguments.get("update", False)
    if not isinstance(update, bool):
        return error_response("update must be a boolean")

    base_payload: dict[str, Any] = {
        "name": name,
        "confidence": confidence,
        "update": update,
    }
    if description:
        base_payload["description"] = description
    if content:
        base_payload["content"] = content
    if priority:
        base_payload["priority"] = priority
    if severity:
        base_payload["severity"] = severity
    if object_marking:
        base_payload["objectMarking"] = object_marking
    if object_label:
        base_payload["objectLabel"] = object_label
    if external_references:
        base_payload["externalReferences"] = external_references
    if objects:
        base_payload["objects"] = objects

    minimal_payload: dict[str, Any] = {"name": name}
    if description:
        minimal_payload["description"] = description
    if update:
        minimal_payload["update"] = update

    errors: list[str] = []
    for mutation_name, input_type in _CREATE_PIR_MUTATIONS:
        mutation = _build_create_mutation(mutation_name, input_type)
        for payload in _payload_candidates(base_payload, minimal_payload):
            try:
                result = await session.execute(gql(mutation), variable_values={"input": payload})
                return success_response(result.get("result", {}))
            except Exception as error:  # noqa: BLE001
                errors.append(str(error))

    last_error = errors[-1] if errors else "unknown schema mismatch"
    return error_response(
        "Unable to create PIR with the available GraphQL schema variants. "
        f"Last error: {last_error}"
    )

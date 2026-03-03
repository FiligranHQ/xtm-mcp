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

_STIX_REF_RELATIONSHIP_ADD_MUTATION = """
mutation AddObjectToCaseRfi($input: StixRefRelationshipAddInput!) {
  result: stixRefRelationshipAdd(input: $input) {
    id
    relationship_type
  }
}
"""

_CASE_RFI_EDIT_RELATION_MUTATION = """
mutation AddObjectToCaseRfi($id: String!, $input: StixRefRelationshipAddInput!) {
  result: caseRfiEdit(id: $id) {
    relationAdd(input: $input) {
      id
    }
  }
}
"""

_CASE_RFI_EDIT_RELATION_MUTATION_ALT = """
mutation AddObjectToCaseRfi($id: String!, $input: RelationAddInput!) {
  result: caseRfiEdit(id: $id) {
    relationAdd(input: $input) {
      id
    }
  }
}
"""


def _build_stix_ref_relationship_variables(
    case_rfi_id: str,
    object_id: str,
) -> dict[str, Any]:
    return {
        "input": {
            "fromId": case_rfi_id,
            "toId": object_id,
            "relationship_type": "object",
        },
    }


def _build_case_rfi_relation_variables(
    case_rfi_id: str,
    object_id: str,
    relationship_key: str,
) -> dict[str, Any]:
    return {
        "id": case_rfi_id,
        "input": {
            "toId": object_id,
            relationship_key: "object",
        },
    }


def _mutation_candidates(case_rfi_id: str, object_id: str) -> list[tuple[str, dict[str, Any]]]:
    return [
        (
            _STIX_REF_RELATIONSHIP_ADD_MUTATION,
            _build_stix_ref_relationship_variables(case_rfi_id, object_id),
        ),
        (
            _CASE_RFI_EDIT_RELATION_MUTATION,
            _build_case_rfi_relation_variables(
                case_rfi_id,
                object_id,
                "relationship_type",
            ),
        ),
        (
            _CASE_RFI_EDIT_RELATION_MUTATION,
            _build_case_rfi_relation_variables(
                case_rfi_id,
                object_id,
                "relationshipType",
            ),
        ),
        (
            _CASE_RFI_EDIT_RELATION_MUTATION_ALT,
            _build_case_rfi_relation_variables(
                case_rfi_id,
                object_id,
                "relationship_type",
            ),
        ),
        (
            _CASE_RFI_EDIT_RELATION_MUTATION_ALT,
            _build_case_rfi_relation_variables(
                case_rfi_id,
                object_id,
                "relationshipType",
            ),
        ),
    ]


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return error_response(_MUTATIONS_DISABLED_MESSAGE)

    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    case_rfi_id, case_rfi_id_error = normalize_non_empty_string(
        arguments.get("id"),
        "id",
        required=True,
    )
    if case_rfi_id_error:
        return error_response(case_rfi_id_error)
    assert case_rfi_id is not None

    object_ids, object_ids_error = normalize_string_list(
        arguments.get("object_ids"),
        "object_ids",
        required=True,
    )
    if object_ids_error:
        return error_response(object_ids_error)
    assert object_ids is not None

    unique_object_ids = list(dict.fromkeys(object_ids))

    added_object_ids: list[str] = []
    mutation_results: list[Any] = []
    failures: list[tuple[str, str]] = []

    for object_id in unique_object_ids:
        candidate_errors: list[str] = []
        for mutation, variables in _mutation_candidates(case_rfi_id, object_id):
            try:
                result = await session.execute(gql(mutation), variable_values=variables)
                added_object_ids.append(object_id)
                mutation_results.append(result.get("result", result))
                break
            except Exception as error:  # noqa: BLE001
                candidate_errors.append(str(error))
        else:
            last_error = candidate_errors[-1] if candidate_errors else "unknown schema mismatch"
            failures.append((object_id, last_error))

    if failures:
        failure_preview = "; ".join(f"{object_id}: {error}" for object_id, error in failures[:3])
        return error_response(
            (
                f"Failed to add {len(failures)} of {len(unique_object_ids)} object(s) "
                f"to case RFI {case_rfi_id}. "
                f"Added: {len(added_object_ids)}. Details: {failure_preview}"
            )
        )

    return success_response(
        {
            "case_rfi_id": case_rfi_id,
            "added_object_ids": added_object_ids,
            "results": mutation_results,
        }
    )

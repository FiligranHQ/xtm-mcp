import re
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_non_empty_string,
    success_response,
)
from opencti_mcp.utils.mutations import mutations_enabled

_OPERATION_PREFIX_PATTERN = re.compile(r"^(query|mutation|subscription)\b", re.IGNORECASE)
_LEADING_WORD_PATTERN = re.compile(r"^([_A-Za-z][_0-9A-Za-z]*)\b")
_MUTATION_OPERATION_LINE_PATTERN = re.compile(r"(?mi)^[ \t]*mutation\b")
_DOCUMENT_PREFIXES = {
    "query",
    "mutation",
    "subscription",
    "fragment",
    "schema",
    "extend",
    "directive",
    "type",
    "interface",
    "union",
    "scalar",
    "enum",
    "input",
}
_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)


def _leading_graphql_token(query_string: str) -> str | None:
    """Return the first significant GraphQL token, skipping blank/comment lines."""
    for line in query_string.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("{"):
            return "{"
        match = _LEADING_WORD_PATTERN.match(stripped)
        if match:
            return match.group(1).lower()
        return None
    return None


def _normalize_graphql_operation(query_string: str) -> str:
    normalized = query_string.strip()
    if _OPERATION_PREFIX_PATTERN.match(normalized):
        return normalized
    leading_token = _leading_graphql_token(normalized)
    if leading_token in _DOCUMENT_PREFIXES:
        return normalized
    return f"query {normalized}"


def _contains_mutation_operation(document: Any, query_string: str) -> bool:
    """Detect whether the GraphQL document includes at least one mutation operation."""
    definitions = getattr(document, "definitions", None)
    if definitions is not None:
        for definition in definitions:
            operation = getattr(definition, "operation", None)
            if operation is None:
                continue
            operation_name = getattr(operation, "value", None)
            if operation_name is None:
                operation_name = str(operation)
            if isinstance(operation_name, str) and operation_name.lower() == "mutation":
                return True

    # Fallback for tests/mocks where gql() may be monkeypatched to return a plain string.
    return bool(_MUTATION_OPERATION_LINE_PATTERN.search(query_string))


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    query_string, query_error = normalize_non_empty_string(
        arguments.get("query"),
        "query",
        required=True,
    )
    if query_error:
        return error_response(query_error)
    assert query_string is not None

    try:
        normalized_query = _normalize_graphql_operation(query_string)
        document = gql(normalized_query)
        if _contains_mutation_operation(document, normalized_query) and not mutations_enabled():
            return error_response(_MUTATIONS_DISABLED_MESSAGE)
        result = await session.execute(document)
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result)

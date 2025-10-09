"""Shared helpers for fetching and processing OpenCTI relationships mapping.

This module centralizes logic used by multiple tools to avoid duplication.
"""

from typing import Any

from gql import gql

from opencti_mcp.graphql_queries import SCHEMA_RELATIONS_TYPES_MAPPING


def build_related_adjacency(mappings: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Build undirected adjacency map: entity -> set(related entities)."""
    related: dict[str, set[str]] = {}
    for mapping in mappings:
        key = mapping.get("key") or ""
        if "_" not in key:
            continue
        left, right = key.split("_", 1)
        if left == right:
            continue
        related.setdefault(left, set()).add(right)
        related.setdefault(right, set()).add(left)
    return related


async def fetch_relationships_mapping_gql(session: Any) -> list[dict[str, Any]]:
    """Fetch schemaRelationsTypesMapping via an existing GraphQL session.

    Uses the shared SCHEMA_RELATIONS_TYPES_MAPPING query and returns a list of
    mapping objects. Returns an empty list if the response shape is unexpected.
    """
    result = await session.execute(gql(SCHEMA_RELATIONS_TYPES_MAPPING))
    data = result if isinstance(result, dict) else {}
    mappings = data.get("schemaRelationsTypesMapping")
    return mappings if isinstance(mappings, list) else []

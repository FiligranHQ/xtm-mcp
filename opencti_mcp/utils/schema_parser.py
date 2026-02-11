"""Utilities to read and interpret the OpenCTI GraphQL schema.

This module fetches the GraphQL Schema Definition Language (SDL) from an OpenCTI
instance, builds a local introspection structure, and provides helpers to
extract common, tool-friendly information:

- list of entity types relevant to STIX domain objects
- simple field maps for a given entity type
- query field names to fetch single and list results for an entity
- a related-entity index derived from the relationships mapping

To construct queries for STIX objects, we need to refer to each entity in four distinct ways:
    GraphQL Type: "AttackPattern",         # The GraphQL type name
    Query Type Singular: "attackPattern",  # The singular query field
    Query Type Plural: "attackPatterns",   # The plural query field
    Relationship Type: "Attack-Pattern",   # The relationship label

The goal is to expose a small, predictable surface that higher-level tools can
use without having to understand the full GraphQL type system.
"""

import re
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from graphql import build_ast_schema, get_introspection_query, graphql_sync, parse

from opencti_mcp.utils.error import SchemaSDLResponseError


def fetch_schema_sdl(opencti_url: str, token: str) -> str:
    """GET OPENCTI_URL/schema and return the 'schema' SDL string.

    Parameters
    - opencti_url: Base URL of the OpenCTI instance.
    - token: Optional bearer token for authenticated instances.
    """
    endpoint = urljoin(opencti_url, "schema")
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = requests.get(endpoint, headers=headers, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = (
            f"Status code: {resp.status_code}; "
            f"Failed to fetch data from {resp.url}. "
            f"Are you sure your OpenCTI version >= 6.8.0 ?"
        )
        raise requests.exceptions.HTTPError(msg) from e

    data = resp.json()
    schema_value = (data or {}).get("schema") if isinstance(data, dict) else None
    if not isinstance(schema_value, str):
        raise SchemaSDLResponseError("/schema did not return JSON object with 'schema' string")
    return schema_value


def build_introspection_from_sdl(schema_sdl: str) -> dict[str, Any]:
    """Build a GraphQL introspection object from SDL.

    Returns the ``__schema`` dictionary as produced by a standard introspection
    query. Raises an error if introspection reports issues or data is missing.
    """
    ast = parse(schema_sdl)
    schema = build_ast_schema(ast)
    result = graphql_sync(schema, get_introspection_query())
    if result.errors:
        raise RuntimeError(f"Introspection failed: {result.errors}")
    data = result.data or {}
    schema_obj = data.get("__schema")
    if not isinstance(schema_obj, dict):
        raise RuntimeError("Introspection result missing __schema")
    return schema_obj


def _collect_types_by_name(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index the top-level GraphQL types by name for quick lookup."""
    types = schema.get("types") or []
    return {t.get("name"): t for t in types if "name" in t}


def _base_named_type(type_obj: dict[str, Any]) -> dict[str, Any]:
    """Resolve through NON_NULL/LIST wrappers to the underlying named type.

    GraphQL type references are nested. This returns the base type dict that
    contains the actual ``name`` and ``kind``.
    """
    t = type_obj
    while t is not None:
        kind = t.get("kind")
        name = t.get("name")
        of_type = t.get("ofType")
        if kind in ("NON_NULL", "LIST") and of_type is not None:
            t = of_type
            continue
        if name is None and of_type is not None:
            t = of_type
            continue
        return t or {}
    return {}


def _type_to_relationship_label(type_name: str) -> str:
    """Convert a type name into a simple relationship label.

    Example:
        >>> _type_to_relationship_label("AttackPattern")
        'Attack-Pattern'
    """
    # Split a CamelCase string into lowercase word tokens.
    tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", type_name)
    if not tokens:
        return type_name
    return "-".join(tokens)


def list_entity_types_by_implements(schema: dict[str, Any]) -> list[str]:
    """Return entity types implementing the core Stix interfaces.

    Filters to objects implementing ``BasicObject``, ``StixObject``,
    ``StixCoreObject``, and either ``StixDomainObject`` (SDO) or
    ``StixCyberObservable`` (SCO). These are the types most relevant to
    higher-level tools, and ensures we include observables such as
    ``IPv4-Addr``.
    """
    needed_all = {"BasicObject", "StixObject", "StixCoreObject"}
    needed_any = {"StixDomainObject", "StixCyberObservable"}
    results: list[str] = []
    for t in schema.get("types") or []:
        if t.get("kind") != "OBJECT":
            continue
        interfaces = {i.get("name") for i in (t.get("interfaces") or []) if i.get("name")}
        if needed_all.issubset(interfaces) and interfaces.intersection(needed_any):
            results.append(t.get("name"))
    return sorted(set([r for r in results if r]))


def _parse_query_fields(schema: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract ``(field_name, base_return_type)`` for fields on the Query type."""
    types_by_name = _collect_types_by_name(schema)
    query_type = types_by_name.get("Query")
    if not query_type:
        return []
    results: list[tuple[str, str]] = []
    for f in query_type.get("fields") or []:
        name = f.get("name")
        base_type = _base_named_type(f.get("type") or {})
        base_name = base_type.get("name")
        if name and base_name:
            results.append((name, base_name))
    return results


def _find_node_type_from_connection(schema: dict[str, Any], connection_type: str) -> str:
    """Given a ``FooConnection`` type, resolve and return the ``Foo`` node type name."""
    types_by_name = _collect_types_by_name(schema)
    conn = types_by_name.get(connection_type)
    if not conn:
        if connection_type.endswith("Connection"):
            return connection_type[:-10]
        return ""
    edge_type_name = ""
    for f in conn.get("fields") or []:
        if f.get("name") != "edges":
            continue
        base_type = _base_named_type(f.get("type") or {})
        base_name = base_type.get("name")
        if base_name and base_name.endswith("Edge"):
            edge_type_name = base_name
            break
    if not edge_type_name:
        if connection_type.endswith("Connection"):
            return connection_type[:-10]
        return ""
    edge_type = types_by_name.get(edge_type_name)
    if not edge_type:
        return ""
    for f in edge_type.get("fields") or []:
        if f.get("name") == "node":
            node_base = _base_named_type(f.get("type") or {})
            return node_base.get("name") or ""
    return ""


def _query_fields_for_entity(
    schema: dict[str, Any],
    entity_type: str,
) -> tuple[Optional[str], Optional[str]]:
    """Find the most likely singular and plural query field names for an entity.

    Returns a tuple of ``(singular_field, plural_field)`` where the plural field
    is inferred from a connection type whose node is the entity.
    """
    singular_name: Optional[str] = None
    plural_name: Optional[str] = None
    for field_name, ret_base in _parse_query_fields(schema):
        if ret_base == entity_type:
            if not singular_name:
                singular_name = field_name
            continue
        if ret_base.endswith("Connection"):
            node_type = _find_node_type_from_connection(schema, ret_base)
            if node_type == entity_type and not plural_name:
                plural_name = field_name
    return singular_name, plural_name


def _normalize_entity_label(label: str) -> str:
    """Normalize relationship labels for matching (alnum + lowercase)."""
    return re.sub(r"[^A-Za-z0-9]", "", label).lower()


def build_related_types_index(
    schema: dict[str, Any], relationships: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Build a map of entity type -> sorted list of related entity types.

    Uses the OpenCTI ``schemaRelationsTypesMapping`` result. Optionally, limit
    the computation to ``restrict_to`` entity types for performance.
    """
    entity_types = list_entity_types_by_implements(schema)
    norm_to_type: dict[str, str] = {_normalize_entity_label(t): t for t in entity_types}
    related_map: dict[str, set] = {t: set() for t in entity_types}
    for rec in relationships:
        key = rec.get("key") or ""
        # `key` field looks like "Attack-Pattern_Malware"
        if not key or "_" not in key:
            continue
        left_label, right_label = key.split("_", 1)
        left_type = norm_to_type.get(_normalize_entity_label(left_label))
        right_type = norm_to_type.get(_normalize_entity_label(right_label))
        if not left_type or not right_type or left_type == right_type:
            continue
        related_map[left_type].add(right_type)
        related_map[right_type].add(left_type)
    return {t: sorted(list(s)) for t, s in related_map.items()}


def parse_type_fields(schema: dict[str, Any], type_name: str) -> dict[str, str]:
    """Return scalar/enum fields for ``type_name`` as ``{field: graphql_scalar}``."""
    types_by_name = _collect_types_by_name(schema)
    t = types_by_name.get(type_name)
    if not t:
        return {}
    fields: dict[str, str] = {}
    for f in t.get("fields") or []:
        fname = f.get("name")
        if not fname:
            continue
        if f.get("args") or []:
            continue
        base_type = _base_named_type(f.get("type") or {})
        base_kind = base_type.get("kind")
        base_name = base_type.get("name")
        if base_kind not in ("SCALAR", "ENUM"):
            continue
        if base_name:
            fields[fname] = base_name
    return fields


def _type_definition(
    schema: dict[str, Any],
    related_index: dict[str, list[str]],
    type_name: str,
) -> dict[str, Any]:
    """Assemble a concise type description consumed by higher-level tools."""
    fields = parse_type_fields(schema, type_name)
    singular_q, plural_q = _query_fields_for_entity(schema, type_name)
    return {
        "fields": fields,
        "query_type_singular": singular_q or "",
        "query_type_plural": plural_q or "",
        "relationship_type": _type_to_relationship_label(type_name),
        "related_types": related_index.get(type_name, []),
    }


class SchemaParser:
    """High-level, convenient access to OpenCTI schema details.

    This class wraps schema parsing utilities to provide a small, stable API
    for tools that need entity types, fields, query names, orderings, and
    related entity types.
    """

    def __init__(
        self,
        schema: dict[str, Any],
        relationships: Optional[list[dict[str, Any]]] = None,
    ):
        """Create a new parser.

        Parameters
        - schema: The GraphQL introspection ``__schema`` object.
        - relationships: Optional mapping from OpenCTI describing related types,
          as returned by ``schemaRelationsTypesMapping``.
        """
        self.schema = schema
        self.entities = list_entity_types_by_implements(schema)
        self._related_index: dict[str, list[str]] = {}
        if relationships is not None:
            self._related_index = build_related_types_index(schema, relationships)

    def get_type_definition(self, entity_type: Any) -> dict[str, Any]:
        """Return the concise type definition for one or many entity types.

        If ``entity_type`` is a collection, returns a dict mapping each input to
        its type definition.
        """
        if isinstance(entity_type, (list, tuple, set)):
            return {str(t): self.get_type_definition(str(t)) for t in entity_type}
        resolved = None
        for t in self.entities:
            if t.lower() == str(entity_type).lower():
                resolved = t
                break
        if resolved is None:
            raise KeyError(f"Unknown entity type: {entity_type}")
        return _type_definition(self.schema, self._related_index, resolved)

    def get_all_type_definitions(self) -> dict[str, dict[str, Any]]:
        """Return concise type definitions for all known entity types."""
        return {t: _type_definition(self.schema, self._related_index, t) for t in self.entities}

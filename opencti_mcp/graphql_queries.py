INTROSPECTION_TYPES = """
query IntrospectionQuery {
  __schema {
    types { name }
  }
}
"""

# opencti_mcp/graphql_queries.py
INTROSPECTION_FULL = """
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      fields {
        name
        type { name kind ofType { name kind } }
      }
    }
  }
}
"""

SCHEMA_RELATIONS_TYPES_MAPPING = """
query StixRelationshipsMapping {
  schemaRelationsTypesMapping { key values }
}
"""

QUERY_FIELDS = """
query {
  __type(name: "Query") {
    fields(includeDeprecated: false) {
      name
      args { name type { name ofType { name } } }
    }
  }
}
"""

SEARCH_ENTITIES_BY_NAME = """
query EntitySearchByName($term: String!) {
  stixCoreObjects(search: $term, orderBy: _score, orderMode: desc, first: 10) {
    edges { node { entity_type } }
  }
}
"""

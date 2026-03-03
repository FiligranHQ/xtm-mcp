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

GET_LICENSE_EDITION_QUERY = """
query GetLicenseEdition {
  settings {
    enterprise_edition
  }
}
"""

GET_LICENSE_EDITION_QUERY_CAMEL = """
query GetLicenseEdition {
  settings {
    enterpriseEdition
  }
}
"""

IDENTITY_PROPERTIES = """
id
standard_id
entity_type
parent_types
spec_version
created_at
updated_at
identity_class
name
description
contact_information
x_opencti_aliases
x_opencti_reliability
... on Individual {
  x_opencti_firstname
  x_opencti_lastname
}
... on Organization {
  x_opencti_organization_type
  x_opencti_score
}
"""

STIX_CORE_OBJECT_BRAND_PROPERTIES = """
id
standard_id
entity_type
parent_types
spec_version
created_at
updated_at
... on StixDomainObject {
  revoked
  confidence
  created
  modified
}
... on AttackPattern {
  name
  description
  aliases
}
... on Campaign {
  name
  description
  aliases
  first_seen
  last_seen
  objective
}
... on CourseOfAction {
  name
  description
}
... on Grouping {
  name
  description
  context
}
... on Identity {
  identity_class
  name
  description
  contact_information
}
... on Indicator {
  name
  description
}
... on Infrastructure {
  name
  description
  aliases
}
... on IntrusionSet {
  name
  description
  aliases
}
... on Malware {
  name
  description
  aliases
}
... on Note {
  attribute_abstract
  content
  note_types
}
... on Organization {
  name
  description
  x_opencti_organization_type
}
... on Report {
  name
  description
  report_types
  published
}
... on ThreatActor {
  name
  description
  aliases
}
... on Tool {
  name
  description
  aliases
}
... on Vulnerability {
  name
  description
}
"""

STIX_CORE_RELATIONSHIP_BRAND_PROPERTIES = """
id
standard_id
entity_type
relationship_type
description
start_time
stop_time
created_at
updated_at
confidence
from {
  ... on BasicObject {
    id
    entity_type
    parent_types
  }
  ... on BasicRelationship {
    id
    entity_type
    parent_types
  }
  ... on StixObject {
    standard_id
  }
  ... on AttackPattern {
    name
  }
  ... on Campaign {
    name
  }
  ... on CourseOfAction {
    name
  }
  ... on Grouping {
    name
  }
  ... on Identity {
    name
  }
  ... on Indicator {
    name
  }
  ... on Infrastructure {
    name
  }
  ... on IntrusionSet {
    name
  }
  ... on Malware {
    name
  }
  ... on Note {
    attribute_abstract
  }
  ... on Report {
    name
  }
  ... on ThreatActor {
    name
  }
  ... on Tool {
    name
  }
  ... on Vulnerability {
    name
  }
}
to {
  ... on BasicObject {
    id
    entity_type
    parent_types
  }
  ... on BasicRelationship {
    id
    entity_type
    parent_types
  }
  ... on StixObject {
    standard_id
  }
  ... on AttackPattern {
    name
  }
  ... on Campaign {
    name
  }
  ... on CourseOfAction {
    name
  }
  ... on Grouping {
    name
  }
  ... on Identity {
    name
  }
  ... on Indicator {
    name
  }
  ... on Infrastructure {
    name
  }
  ... on IntrusionSet {
    name
  }
  ... on Malware {
    name
  }
  ... on Note {
    attribute_abstract
  }
  ... on Report {
    name
  }
  ... on ThreatActor {
    name
  }
  ... on Tool {
    name
  }
  ... on Vulnerability {
    name
  }
}
"""

LIST_IDENTITIES_QUERY = f"""
query ListIdentities(
  $types: [String]
  $search: String
  $first: Int
  $after: ID
  $orderBy: IdentitiesOrdering
  $orderMode: OrderingMode
) {{
  identities(
    types: $types
    search: $search
    first: $first
    after: $after
    orderBy: $orderBy
    orderMode: $orderMode
  ) {{
    edges {{
      node {{
        {IDENTITY_PROPERTIES}
      }}
    }}
    pageInfo {{
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }}
  }}
}}
"""

READ_IDENTITY_QUERY = f"""
query ReadIdentity($id: String!) {{
  identity(id: $id) {{
    {IDENTITY_PROPERTIES}
  }}
}}
"""

LIST_STIX_CORE_OBJECTS_QUERY = f"""
query ListStixCoreObjects(
  $types: [String]
  $search: String
  $first: Int
  $after: ID
  $orderBy: StixCoreObjectsOrdering
  $orderMode: OrderingMode
) {{
  stixCoreObjects(
    types: $types
    search: $search
    first: $first
    after: $after
    orderBy: $orderBy
    orderMode: $orderMode
  ) {{
    edges {{
      node {{
        {STIX_CORE_OBJECT_BRAND_PROPERTIES}
      }}
    }}
    pageInfo {{
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }}
  }}
}}
"""

READ_STIX_CORE_OBJECT_QUERY = f"""
query ReadStixCoreObject($id: String!) {{
  stixCoreObject(id: $id) {{
    {STIX_CORE_OBJECT_BRAND_PROPERTIES}
  }}
}}
"""

LIST_STIX_CORE_RELATIONSHIPS_QUERY = f"""
query ListStixCoreRelationships(
  $fromOrToId: [String]
  $fromId: [String]
  $toId: [String]
  $relationship_type: [String]
  $search: String
  $first: Int
  $after: ID
  $orderBy: StixCoreRelationshipsOrdering
  $orderMode: OrderingMode
) {{
  stixCoreRelationships(
    fromOrToId: $fromOrToId
    fromId: $fromId
    toId: $toId
    relationship_type: $relationship_type
    search: $search
    first: $first
    after: $after
    orderBy: $orderBy
    orderMode: $orderMode
  ) {{
    edges {{
      node {{
        {STIX_CORE_RELATIONSHIP_BRAND_PROPERTIES}
      }}
    }}
    pageInfo {{
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }}
  }}
}}
"""

READ_STIX_CORE_RELATIONSHIP_QUERY = f"""
query ReadStixCoreRelationship($id: String!) {{
  stixCoreRelationship(id: $id) {{
    {STIX_CORE_RELATIONSHIP_BRAND_PROPERTIES}
  }}
}}
"""

LIST_MARKING_DEFINITIONS_QUERY = """
query ListMarkingDefinitions(
  $first: Int
  $after: ID
  $orderBy: MarkingDefinitionsOrdering
  $orderMode: OrderingMode
) {
  markingDefinitions(
    first: $first
    after: $after
    orderBy: $orderBy
    orderMode: $orderMode
  ) {
    edges {
      node {
        id
        standard_id
        entity_type
        parent_types
        definition_type
        definition
        x_opencti_order
        x_opencti_color
        created
        modified
        created_at
        updated_at
      }
    }
    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }
  }
}
"""

READ_MARKING_DEFINITION_QUERY = """
query ReadMarkingDefinition($id: String!) {
  markingDefinition(id: $id) {
    id
    standard_id
    entity_type
    parent_types
    definition_type
    definition
    x_opencti_order
    x_opencti_color
    created
    modified
    created_at
    updated_at
  }
}
"""

LIST_LABELS_QUERY = """
query ListLabels(
  $search: String
  $first: Int
  $after: ID
  $orderBy: LabelsOrdering
  $orderMode: OrderingMode
) {
  labels(
    search: $search
    first: $first
    after: $after
    orderBy: $orderBy
    orderMode: $orderMode
  ) {
    edges {
      node {
        id
        value
        color
        created_at
        updated_at
        standard_id
      }
    }
    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
      globalCount
    }
  }
}
"""

READ_LABEL_QUERY = """
query ReadLabel($id: String!) {
  label(id: $id) {
    id
    value
    color
    created_at
    updated_at
    standard_id
  }
}
"""

CREATE_IDENTITY_MUTATION = """
mutation CreateIdentity($input: IdentityAddInput!) {
  identityAdd(input: $input) {
    id
    standard_id
    entity_type
    parent_types
    identity_class
    name
    description
  }
}
"""

CREATE_ORGANIZATION_MUTATION = """
mutation CreateOrganization($input: OrganizationAddInput!) {
  organizationAdd(input: $input) {
    id
    standard_id
    entity_type
    parent_types
    identity_class
    name
    description
    x_opencti_organization_type
  }
}
"""

CREATE_GROUPING_MUTATION = """
mutation CreateGrouping($input: GroupingAddInput!) {
  groupingAdd(input: $input) {
    id
    standard_id
    entity_type
    parent_types
    name
    context
    description
  }
}
"""

CREATE_EXTERNAL_REFERENCE_MUTATION = """
mutation CreateExternalReference($input: ExternalReferenceAddInput!) {
  externalReferenceAdd(input: $input) {
    id
    standard_id
    entity_type
    source_name
    description
    url
    external_id
  }
}
"""

CREATE_LABEL_MUTATION = """
mutation CreateLabel($input: LabelAddInput!) {
  labelAdd(input: $input) {
    id
    value
    color
    created_at
    updated_at
    standard_id
  }
}
"""

CREATE_REPORT_MUTATION = """
mutation CreateReport($input: ReportAddInput!) {
  reportAdd(input: $input) {
    id
    standard_id
    name
    description
    report_types
    published
    confidence
  }
}
"""

ADD_NOTE_MUTATION = """
mutation AddNote($input: NoteAddInput!) {
  noteAdd(input: $input) {
    id
    standard_id
    attribute_abstract
    content
    note_types
    confidence
  }
}
"""

CREATE_RELATIONSHIP_MUTATION = """
mutation CreateRelationship($input: StixCoreRelationshipAddInput!) {
  stixCoreRelationshipAdd(input: $input) {
    id
    standard_id
    relationship_type
  }
}
"""

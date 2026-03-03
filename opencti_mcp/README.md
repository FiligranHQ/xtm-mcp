# OpenCTI GraphQL MCP Server

MCP server to interact with OpenCTI through GraphQL for:
- schema discovery
- threat data retrieval
- brand posture workflows (read + publish back to OpenCTI)

## Requirements

- Python 3.10+
- OpenCTI URL + API token

Install dependencies from repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

You can pass credentials via CLI flags or environment variables (`.env` supported).

```bash
cp .env.example .env
# edit .env
# OPENCTI_URL=https://your-opencti
# OPENCTI_TOKEN=<token>
```

Variables:
- `OPENCTI_URL`: OpenCTI base URL (the server appends `/graphql`)
- `OPENCTI_TOKEN`: API token
- `OPENCTI_ENABLE_MUTATIONS`: optional boolean (`true/false`, `1/0`, `yes/no`, `on/off`)

## Run

### STDIO (default)

```bash
python -m opencti_mcp.server --url "https://your-opencti" --token "<token>"
```

### STDIO with mutations enabled

```bash
python -m opencti_mcp.server \
  --enable-mutations \
  --url "https://your-opencti" \
  --token "<token>"
```

### Streamable HTTP

```bash
python -m opencti_mcp.server \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --url "https://your-opencti" \
  --token "<token>"
```

### SSE

```bash
python -m opencti_mcp.server \
  --transport sse \
  --host 127.0.0.1 \
  --port 8000 \
  --url "https://your-opencti" \
  --token "<token>"
```

## MCP Client Config Examples

### STDIO

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "command": "python",
      "args": ["-m", "opencti_mcp.server"],
      "env": {
        "OPENCTI_URL": "https://your-opencti",
        "OPENCTI_TOKEN": "<token>"
      }
    }
  }
}
```

### Streamable HTTP

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

## Mutation Safety

Mutation tools are exposed but blocked by default.

To enable them, use:
- `--enable-mutations`, or
- `OPENCTI_ENABLE_MUTATIONS=true`

Mutation tools:
- `create_identity`
- `create_label`
- `create_external_reference`
- `create_grouping`
- `create_pir`
- `create_case_rfi`
- `add_objects_to_case_rfi`
- `create_report`
- `add_note`
- `create_relationship`

## Available Tools

### 1) Schema and Query Helpers

| Tool | Purpose |
| --- | --- |
| `list_graphql_types` | List all GraphQL types from introspection |
| `get_types_definitions` | Return field definitions for one or several types |
| `get_types_definitions_from_schema` | Parse OpenCTI `/schema` SDL and return all type definitions |
| `get_query_fields` | List GraphQL `Query` fields and arguments |
| `validate_graphql_query` | Validate a query string against OpenCTI |
| `execute_graphql_query` | Execute a GraphQL operation string (`query`, `mutation`, `subscription`) |
| `get_stix_relationships_mapping` | Return available STIX relationship mappings |
| `get_entity_names` | Return unique entity names extracted from relationship mapping |
| `search_entities_by_name` | Search entities by name and intersect with available entity types |

Notes:
- `execute_graphql_query` keeps explicit GraphQL document prefixes unchanged (`query`, `mutation`, `subscription`, `fragment`, etc.).
- If no document prefix is provided, `execute_graphql_query` prepends `query`.
- `mutation` operations submitted through `execute_graphql_query` follow the same mutation gate (`--enable-mutations` / `OPENCTI_ENABLE_MUTATIONS=true`) as dedicated write tools.
- For write operations, use dedicated mutation tools.

### 2) Brand Posture Read Pack

| Tool | Purpose |
| --- | --- |
| `get_license_edition` | Detect if instance is `CE` or `EE` |
| `list_identities` | List brand/supplier/subsidiary identities |
| `read_identity` | Read a single identity by ID |
| `list_stix_core_objects` | List reports, campaigns, threat actors, malware, tools, vulnerabilities, etc. |
| `read_stix_core_object` | Read one STIX Core Object by ID |
| `list_stix_core_relationships` | List relationships for pivoting and explainability |
| `read_stix_core_relationship` | Read one STIX Core Relationship by ID |
| `list_marking_definitions` | List markings (TLP, statements, etc.) |
| `read_marking_definition` | Read one marking definition by ID |
| `list_labels` | List labels |
| `read_label` | Read one label by ID |
| `list_pirs` | List priority intelligence requirements |
| `read_pir` | Read one PIR by ID |
| `list_case_rfis` | List case RFIs |
| `read_case_rfi` | Read one case RFI by ID |

### 3) Brand Posture Publish Pack (mutations enabled)

| Tool | Purpose |
| --- | --- |
| `create_identity` | Create an identity (organization, individual, system, etc.) |
| `create_label` | Create a label |
| `create_external_reference` | Create source references (advisory, case URL, portal, etc.) |
| `create_grouping` | Bundle objects used in a pulse |
| `create_pir` | Create a PIR |
| `create_case_rfi` | Create a case RFI |
| `add_objects_to_case_rfi` | Attach one or more objects to a case RFI |
| `create_report` | Create a report |
| `add_note` | Create a note attached to one or more objects |
| `create_relationship` | Create a STIX core relationship |

## Typical Brand Pulse Flow

1. Detect platform capabilities:
   - `get_license_edition`
2. Scope identities:
   - `list_identities`
   - `read_identity`
3. Collect threat context:
   - `list_stix_core_objects` (reports, campaigns, threat actors, malware, tools, vulnerabilities)
   - `list_stix_core_relationships`
4. Prepare classification:
   - `list_marking_definitions`
   - `list_labels`
5. Publish pulse:
   - `create_external_reference`
   - `create_label` (optional)
   - `create_grouping` (optional)
   - `add_note` and/or `create_report`
   - `create_relationship`

## Testing

From repository root:

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Notes on OpenCTI Schema Access

- GraphQL introspection queries (`/graphql`) are commonly disabled in production OpenCTI.
- `/schema` endpoint is available from OpenCTI 6.8+.

This server supports both:
- Introspection-based tools: `list_graphql_types`, `get_types_definitions`, `get_query_fields`
- SDL-based tool: `get_types_definitions_from_schema`

If introspection tools fail, verify OpenCTI configuration as described in official docs:
https://docs.opencti.io/latest/deployment/configuration/?h=introspection#technical-customization

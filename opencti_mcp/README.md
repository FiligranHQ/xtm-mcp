# OpenCTI GraphQL MCP server

Tools and a server to interact with OpenCTI's GraphQL API via MCP.

## Motivation

The goal of this MCP server is to provide an interface for interacting with an OpenCTI instance via its GraphQL API. To achieve this, we define a set of tools that help the agent introspect the schema, list available types and corresponding fields, and run or validate queries against your OpenCTI server. At this point, we focus on queries (i.e. reading the data). We plan to handle mutations in the near future.

## Python compatibility

- Tested with Python 3.10+
- The codebase targets Python 3.10 (see `pyproject.toml` mypy config). Newer versions (3.11/3.12) should work as well.

## Install

Run the following from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Provide credentials via CLI flags or environment variables. `.env` is supported (see `.env.example`). Use the base URL of your OpenCTI; the server will automatically call the `/graphql` endpoint.

```bash
cp .env.example .env
# then edit .env to set OPENCTI_URL and OPENCTI_TOKEN
```

- `OPENCTI_URL` – Base URL of your OpenCTI (e.g., `https://your-opencti`). The server appends `/graphql`.
- `OPENCTI_TOKEN` – API token

## Run

```bash
python -m opencti_mcp.server --url "https://your-opencti/" --token "<token>"
```

## MCP client configuration

Configure your MCP-enabled client to launch this server. Example configuration:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "command": "python",
      "args": ["-m", "opencti_mcp.server"],
      "env": {
        "OPENCTI_URL": "https://your-opencti/",
        "OPENCTI_TOKEN": "<token>"
      }
    }
  }
}
```

Alternatively, you can omit `env` and pass flags via `args`, e.g.:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "command": "python",
      "args": [
        "-m", "opencti_mcp.server",
        "--url",
        "https://your-opencti/",
        "--token",
        "<token>"
      ]
    }
  }
}
```

## Available tools

- `list_graphql_types`: Fetch and return the list of all GraphQL types.
  - Inputs: none
  - Outputs: JSON array of type names

- `get_types_definitions`: Fetch and return the definition of one or more GraphQL types.
  - Inputs:
    - `type_name` (required): string or JSON array (or JSON-stringified array) of type names
  - Outputs: JSON array of objects, each shaped as `{ "<TypeName>": [{ "name": string, "type": string|null, "kind": string|null }] }`
  - Errors: returns a text error message if `type_name` missing or of wrong type

- `get_types_definitions_from_schema`: Return all type definitions using `/schema`.
  - Inputs: none (reads `OPENCTI_URL` and `OPENCTI_TOKEN` from environment/.env)
  - Outputs: JSON object mapping type name to type definition (fields, queries, relationship_type, related_types)

- `execute_graphql_query`: Execute a GraphQL query and return the result.
  - Inputs:
    - `query` (required): GraphQL query string; if it does not start with `query`, the server will prepend `query`
  - Outputs: JSON object `{ "success": true, "data": <GraphQL result> }` on success
  - Errors: JSON object `{ "success": false, "error": string }` on failure

- `validate_graphql_query`: Validate a GraphQL query without returning its result.
  - Inputs:
    - `query` (required): GraphQL query string; if it does not start with `query`, the server will prepend `query`
  - Outputs: JSON object `{ "success": true, "error": "" }` if the query validates and executes successfully
  - Errors: JSON object `{ "success": false, "error": string }` if validation/execution fails

- `get_stix_relationships_mapping`: Get all possible STIX relationships between types and their available relationship types.
  - Inputs:
    - `type_name` (optional): filter to a specific type name; if provided, returns only related entities for this type
  - Outputs:
    - With filter: JSON object `{ "filtered_type": string, "relationships_mapping": string[] }`
    - Without filter: JSON object `{ "relationships_mapping": { [typeName: string]: string[] } }`

- `get_query_fields`: Get all field names from the GraphQL `Query` type.
  - Inputs: none
  - Outputs: JSON object `{ "query_fields": [{ "name": string, "args": [{ "name": string, "type": string|null }] }] }` (sorted by field name)
  - Errors: text error if the `Query` type is not found

- `get_entity_names`: Get all unique entity names from STIX relationships mapping.
  - Inputs: none
  - Outputs: JSON object `{ "entity_names": string[], "count": number }`

- `search_entities_by_name`: Search for entities by name and intersect with available entity types.
  - Inputs:
    - `entity_name` (required): non-empty string to search for
  - Outputs: JSON array of entity type strings present in both search results and available schema types
  - Errors: text error if `entity_name` missing or empty

### Example output

Example output for `list_graphql_types`:

```json
[
  "AttackPattern",
  "Campaign",
  "Note",
  "User"
]
```

## Example Workflow

A typical agent workflow proceeds as follows:

1. Receive a question from the user.
2. Analyze (introspect) the GraphQL schema to identify which types are relevant to the user's question.
3. Retrieve the definitions of these types to understand their relevant fields.
4. Construct a GraphQL query that can answer the user's question.
5. Execute the query and return the response to the user.

## Notes on schema access

- GraphQL introspection queries (via `/graphql`) is disabled by default in OpenCTI.
- The `/schema` endpoint is available from OpenCTI 6.8.0 onwards and returns the schema SDL.
- This MCP supports both approaches:
  - Tools that rely on `/graphql` introspection (e.g., `get_types_definitions`). In this case, the introspection queries should be activated in your OpenCTI setup.
  - Tools that load SDL from `/schema` and introspect locally (e.g., `get_types_definitions_from_schema`)

## Development

Install developer tooling (ruff, black, mypy):

```bash
pip install -r requirements-dev.txt
```

Run checks:

```bash
ruff check .
black .
mypy .
```

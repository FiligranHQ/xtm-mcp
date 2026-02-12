# OpenCTI GraphQL MCP server

Tools and a server to interact with OpenCTI's GraphQL API via MCP.

## Motivation

The goal of this MCP server is to provide an interface for interacting with an OpenCTI instance via its GraphQL API. To achieve this, we define a set of tools that help the agent introspect the schema, list available types and corresponding fields, and run or validate queries against your OpenCTI server. At this point, we focus on queries (i.e. reading the data). We plan to handle mutations in the near future.

> For environment setup (venv, dependencies) and developer tooling, see the [root README](../README.md).

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
# STDIO transport (default)
python -m opencti_mcp.server --url "https://your-opencti/" --token "<token>"

# Explicitly select STDIO transport
python -m opencti_mcp.server --transport stdio --url "https://your-opencti/" --token "<token>"

# Streamable HTTP transport (recommended for remote / browser-based clients)
python -m opencti_mcp.server \
  --transport streamable-http \
  --host "127.0.0.1" \
  --port 8000 \
  --url "https://your-opencti/" \
  --token "<token>"

# SSE transport (legacy HTTP streaming)
python -m opencti_mcp.server \
  --transport sse \
  --host "127.0.0.1" \
  --port 8000 \
  --url "https://your-opencti/" \
  --token "<token>"
```

## MCP client configuration

Configure your MCP-enabled client to connect to this server. The JSON config differs depending on the transport.

### STDIO (default)

The client launches the server process automatically:

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

### SSE

For SSE, the server must be started separately first (see the `--transport sse` command above). The client then connects to the running server:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

### Streamable HTTP

For streamable HTTP, the server must be started separately first (see the `--transport streamable-http` command above). The client then connects to the running server:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## Testing the server

After starting the server you can quickly verify each transport is working.

### STDIO

STDIO communicates over stdin/stdout pipes, so it cannot be tested with `curl`. You can pipe a JSON-RPC `initialize` message directly to the server process:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | python -m opencti_mcp.server --url "$OPENCTI_URL" --token "$OPENCTI_TOKEN"
```

A successful response is a JSON object containing `serverInfo` and `capabilities`.

Alternatively, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

### SSE

With the server running on `--transport sse`, open the event stream with `curl`:

```bash
curl -N http://127.0.0.1:8000/sse
```

A successful connection immediately receives an `event: endpoint` line followed by a `data:` payload containing the message posting URL.

### Streamable HTTP

With the server running on `--transport streamable-http`, send an `initialize` request:

```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

A successful response is a JSON object containing `serverInfo` and `capabilities`.

> **Note:** A plain `GET http://127.0.0.1:8000/mcp` returns `406 Not Acceptable` — this is expected. The streamable HTTP protocol requires specific `Accept` and `Content-Type` headers (see above).

### Automated test suite

The project includes an automated test suite that validates all three transports end-to-end with a mocked GraphQL backend (no real OpenCTI instance needed):

```bash
pip install -r requirements-dev.txt
pytest tests/
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

The following tools rely on GraphQL **introspection queries**:

- `list_graphql_types`
- `get_types_definitions`
- `get_query_fields`

Even though they are enabled by default, most OpenCTI environments disable **introspection queries**. To use these tools, check your OpenCTI configuration as described in the [relevant documentation](https://docs.opencti.io/latest/deployment/configuration/?h=introspection#technical-customization). Namely, you need the environment variables:

* `APP__GRAPHQL__PLAYGROUND__FORCE_DISABLED_INTROSPECTION` set to `true` (default)
* `APP__GRAPHQL__PLAYGROUND__ENABLED` set to `true` (default)

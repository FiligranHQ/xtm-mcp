# OpenCTI GraphQL MCP server

Tools and a server to interact with OpenCTI's GraphQL API via MCP.

## Motivation

The goal of this MCP server is to provide an interface for interacting with an OpenCTI instance via its GraphQL API. To achieve this, we define a set of tools that help the agent introspect the schema, list available types and corresponding fields, and run or validate queries against your OpenCTI server. At this point, we focus on queries (i.e. reading the data). We plan to handle mutations in the near future.

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
- `get_types_definitions`: Fetch and return the definition of one or more GraphQL types.
  - `inputs`: `type_name` (string or array of strings; required)
- `execute_graphql_query`: Execute a GraphQL query and return the result.
  - `inputs`: `query` (string; required)
- `validate_graphql_query`: Validate a GraphQL query without returning its result.
  - `inputs`: `query` (string; required)
- `get_stix_relationships_mapping`: Get all possible STIX relationships between types and their available relationship types.
  - `inputs`: `type_name` (string; optional filter)
- `get_query_fields`: Get all field names from the GraphQL `Query` type.
- `get_entity_names`: Get all unique entity names from STIX relationships mapping.
- `search_entities_by_name`: Search for entities by name and intersect with available entity types.
  - `inputs`: `entity_name` (string; required)

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

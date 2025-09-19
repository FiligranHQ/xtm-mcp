# XTM MCP Servers

This repository hosts MCP (Model Context Protocol) servers related to Filigran's XTM Suite. The first server targets OpenCTI's GraphQL API and can be found in `opencti_mcp`. More MCP servers to come!

## Versioning strategy
This repository follows Semantic Versioning (SemVer) with the version format `X.Y.Z`, where:
- X (Major): Incremented for significant changes that introduce breaking changes or major new features that are not backward-compatible. 
- Y (Minor): Incremented for new features or enhancements that are backward-compatible. Example: adding a new MCP server for one of the tools in the XTM suite
- Z (Patch): Incremented for bug fixes or minor updates that are backward-compatible

Versions are tagged in the format X.Y.Z (e.g., 1.0.0) in the GitHub repository.

## Specific configuration

### Opencti MCP server
These following tools rely on GraphQL **introspection queries** : 

- list_graphql_types
- get_types_definitions
- get_query_fields

Even though they are enabled by default, most of OpenCTI environments disable **introspection queries**. To use these tools, you will have to check your OpenCTI configuration, as described in the [relevant documentation](https://docs.opencti.io/latest/deployment/configuration/?h=introspection#technical-customization). Namely, you have to have the environment variables :
* `APP__GRAPHQL__PLAYGROUND__FORCE_DISABLED_INTROSPECTION` set to `true` (default)
* `APP__GRAPHQL__PLAYGROUND__ENABLED` set to `true` (default).


## Requirements

- Python 3.10+
- pip and venv (or your preferred environment manager)

## Quickstart (OpenCTI MCP)

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment (create `.env` or export variables):

   Option A (.env)
   ```bash
   cp .env.example .env
   # then edit .env to set:
   # OPENCTI_URL=https://your-opencti
   # OPENCTI_TOKEN=<your-token>
   ```

   Option B (environment variables)
   ```bash
   export OPENCTI_URL="https://your-opencti"
   export OPENCTI_TOKEN="<your-token>"
   ```

   Note: Provide the base URL; the server will automatically use the `/graphql` endpoint.

3. Run the server:
```bash
python -m opencti_mcp.server --url "$OPENCTI_URL" --token "$OPENCTI_TOKEN"
```

For MCP client configuration and detailed tool documentation, see `opencti_mcp/README.md`.

## MCP client configuration (quick copy)

If your MCP-enabled client supports JSON config, a minimal setup looks like:

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

Alternatively pass flags:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "command": "python",
      "args": [
        "-m", "opencti_mcp.server",
        "--url", "https://your-opencti/",
        "--token", "<token>"
      ]
    }
  }
}
```

## Development

Install developer tooling (ruff, black, mypy):

```bash
pip install -r requirements-dev.txt
```

Run checks:

```bash
# Lint
ruff check .

# Format
black .

# Type-check
mypy .
```

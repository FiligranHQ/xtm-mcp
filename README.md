# XTM One

This repository hosts MCP (Model Context Protocol) servers related to Filigran's XTM Suite. The first server targets OpenCTI's GraphQL API and can be found in `opencti_mcp`. More MCP servers to come!

## Requirements

- Python 3.10+
- Poetry for dependency management

## Quickstart (OpenCTI MCP)

1. Install dependencies:
```bash
poetry install
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
poetry run opencti-mcp --url "$OPENCTI_URL" --token "$OPENCTI_TOKEN"
```

For MCP client configuration and detailed tool documentation, see `opencti_mcp/README.md`.

## MCP client configuration (quick copy)

If your MCP-enabled client supports JSON config, a minimal setup looks like:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "command": "poetry",
      "args": ["run", "opencti-mcp"],
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
      "command": "poetry",
      "args": [
        "run",
        "opencti-mcp",
        "--url", "https://your-opencti/",
        "--token", "<token>"
      ]
    }
  }
}
```

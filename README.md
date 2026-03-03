# XTM MCP Servers

This repository hosts MCP (Model Context Protocol) servers for Filigran products.

At the moment it includes one server:

| Server | Directory | Description |
| --- | --- | --- |
| OpenCTI GraphQL MCP | [`opencti_mcp/`](opencti_mcp/README.md) | Query and mutate OpenCTI from MCP clients (schema discovery, threat intel retrieval, brand posture workflows). |

## Requirements

- Python 3.10+
- `pip` + `venv` (or an equivalent environment manager)
- OpenCTI instance URL and API token

## Quickstart (use the server)

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure credentials:

```bash
cp .env.example .env
# edit .env and set:
# OPENCTI_URL=https://your-opencti
# OPENCTI_TOKEN=<your-token>
```

3. Run the MCP server (STDIO):

```bash
python -m opencti_mcp.server
```

4. Enable write tools only when needed:

```bash
python -m opencti_mcp.server --enable-mutations
```

Note:
- `--enable-mutations` only affects this MCP server process.
- It is a local safety guard to avoid exposing write-capable MCP servers by default.
- It does not change permissions/capabilities on the remote OpenCTI/OEAV instance.
- The target backend and token permissions must allow mutations, otherwise writes will still fail.

5. Connect from your MCP client. Example config:

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

6. Deploy over HTTP when needed.

Streamable HTTP server:

```bash
python -m opencti_mcp.server \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000
```

Streamable HTTP MCP client config:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

SSE server:

```bash
python -m opencti_mcp.server \
  --transport sse \
  --host 127.0.0.1 \
  --port 8000
```

SSE MCP client config:

```json
{
  "mcpServers": {
    "opencti-graphql-mcp": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

For full transport options and all tools, see [`opencti_mcp/README.md`](opencti_mcp/README.md).

## Development

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run checks:

```bash
ruff check .
black .
mypy .
pytest tests/
```

## Contributing

Contributions are welcome, including documentation improvements, bug fixes, and new tools.

1. Create a feature branch from `main`.
2. Implement changes and tests.
3. Run `ruff`, `mypy`, and `pytest`.
4. Open a PR with:
  - clear problem statement
  - implementation details
  - test evidence

Please read:
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Versioning

The project follows Semantic Versioning (`X.Y.Z`):
- `X`: breaking changes
- `Y`: backward-compatible features
- `Z`: backward-compatible fixes

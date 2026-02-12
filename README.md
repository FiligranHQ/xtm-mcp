# XTM MCP Servers

This repository hosts MCP (Model Context Protocol) servers related to Filigran's XTM Suite. More MCP servers to come!

## Versioning strategy
This repository follows Semantic Versioning (SemVer) with the version format `X.Y.Z`, where:
- X (Major): Incremented for significant changes that introduce breaking changes or major new features that are not backward-compatible. 
- Y (Minor): Incremented for new features or enhancements that are backward-compatible. Example: adding a new MCP server for one of the tools in the XTM suite
- Z (Patch): Incremented for bug fixes or minor updates that are backward-compatible

Versions are tagged in the format X.Y.Z (e.g., 1.0.0) in the GitHub repository.

## Available servers

| Server | Directory | Description |
|--------|-----------|-------------|
| OpenCTI GraphQL MCP | [`opencti_mcp/`](opencti_mcp/README.md) | Interact with an OpenCTI instance via its GraphQL API — introspect the schema, list types, run and validate queries. |

See each server's README for configuration, usage, available tools, and MCP client setup.

## Requirements

- Python 3.10+
- pip and venv (or your preferred environment manager)

## Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Follow the server-specific README for configuration and usage (e.g. [`opencti_mcp/README.md`](opencti_mcp/README.md)).

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

# Run tests
pytest tests/
```

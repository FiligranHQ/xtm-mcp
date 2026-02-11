"""Minimal MCP server entry-point for STDIO transport tests.

Launched as a subprocess by ``test_transport_stdio.py``.  It creates a
``FastMCP`` instance with the mock lifespan (no real OpenCTI needed) and
runs over STDIO.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so ``tests.conftest`` can be imported.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tests.conftest import create_test_server  # noqa: E402


def main() -> None:
    server = create_test_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from unittest.mock import AsyncMock

from opencti_mcp.tools import execute_graphql_query as execute_graphql_query_tool


async def test_execute_graphql_query_prefixes_query_when_no_operation(monkeypatch):
    monkeypatch.setattr(execute_graphql_query_tool, "gql", lambda query: query)
    session = AsyncMock()
    session.execute.return_value = {"viewer": {"id": "user--1"}}

    result = await execute_graphql_query_tool.handle(session, {"query": "{ viewer { id } }"})

    payload = json.loads(result[0].text)
    assert payload == {"success": True, "data": {"viewer": {"id": "user--1"}}}
    assert session.execute.await_count == 1
    sent_query = session.execute.await_args.args[0]
    assert sent_query.startswith("query ")


async def test_execute_graphql_query_accepts_mutation_without_forcing_query(monkeypatch):
    monkeypatch.setattr(execute_graphql_query_tool, "gql", lambda query: query)
    session = AsyncMock()
    session.execute.return_value = {"result": {"id": "x"}}

    result = await execute_graphql_query_tool.handle(
        session,
        {"query": "mutation DoThing { ping }"},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert session.execute.await_count == 1
    sent_query = session.execute.await_args.args[0]
    assert sent_query.startswith("mutation ")
    assert not sent_query.startswith("query mutation ")


async def test_execute_graphql_query_returns_json_error_for_invalid_arguments():
    session = AsyncMock()

    result = await execute_graphql_query_tool.handle(session, {"query": ""})

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "query" in payload["error"]
    session.execute.assert_not_called()

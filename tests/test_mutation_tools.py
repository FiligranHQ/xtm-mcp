from __future__ import annotations

import json
from unittest.mock import AsyncMock

from opencti_mcp.tools import add_note as add_note_tool
from opencti_mcp.tools import create_relationship as create_relationship_tool
from opencti_mcp.tools import create_report as create_report_tool


async def test_create_report_is_blocked_when_mutations_disabled(monkeypatch):
    monkeypatch.delenv("OPENCTI_ENABLE_MUTATIONS", raising=False)
    session = AsyncMock()

    result = await create_report_tool.handle(
        session,
        {"name": "Report A", "description": "Body"},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "disabled" in payload["error"].lower()
    session.execute.assert_not_called()


async def test_create_report_executes_with_expected_payload(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"reportAdd": {"id": "report--1", "name": "Report A"}}

    result = await create_report_tool.handle(
        session,
        {
            "name": "Report A",
            "description": "Body",
            "report_types": ["threat-report"],
            "published": "2026-02-24T00:00:00.000Z",
            "confidence": 90,
            "objects": ["indicator--1"],
            "labels": ["malware"],
        },
    )

    payload = json.loads(result[0].text)
    assert payload == {"success": True, "data": {"id": "report--1", "name": "Report A"}}

    assert session.execute.await_count == 1
    assert session.execute.await_args.kwargs["variable_values"] == {
        "input": {
            "name": "Report A",
            "description": "Body",
            "report_types": ["threat-report"],
            "published": "2026-02-24T00:00:00.000Z",
            "confidence": 90,
            "objects": ["indicator--1"],
            "objectLabel": ["malware"],
        }
    }


async def test_add_note_requires_objects(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()

    result = await add_note_tool.handle(
        session,
        {"content": "Note body"},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "objects" in payload["error"]
    session.execute.assert_not_called()


async def test_create_relationship_executes_with_expected_payload(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {
        "stixCoreRelationshipAdd": {
            "id": "relationship--1",
            "relationship_type": "related-to",
        }
    }

    result = await create_relationship_tool.handle(
        session,
        {
            "fromId": "indicator--1",
            "toId": "malware--1",
            "relationship_type": "related-to",
        },
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["id"] == "relationship--1"

    assert session.execute.await_count == 1
    assert session.execute.await_args.kwargs["variable_values"] == {
        "input": {
            "fromId": "indicator--1",
            "toId": "malware--1",
            "relationship_type": "related-to",
        }
    }

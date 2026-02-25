from __future__ import annotations

import json
from unittest.mock import AsyncMock

from opencti_mcp.tools import add_objects_to_case_rfi as add_objects_to_case_rfi_tool
from opencti_mcp.tools import create_case_rfi as create_case_rfi_tool
from opencti_mcp.tools import create_pir as create_pir_tool
from opencti_mcp.tools import list_pirs as list_pirs_tool


async def test_create_pir_is_blocked_when_mutations_disabled(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "false")
    session = AsyncMock()

    result = await create_pir_tool.handle(session, {"name": "PIR A"})

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "disabled" in payload["error"].lower()
    session.execute.assert_not_called()


async def test_create_case_rfi_is_blocked_when_mutations_disabled(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "false")
    session = AsyncMock()

    result = await create_case_rfi_tool.handle(session, {"name": "RFI A"})

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "disabled" in payload["error"].lower()
    session.execute.assert_not_called()


async def test_add_objects_to_case_rfi_is_blocked_when_mutations_disabled(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "false")
    session = AsyncMock()

    result = await add_objects_to_case_rfi_tool.handle(
        session,
        {"id": "case-rfi--1", "object_ids": ["indicator--1"]},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "disabled" in payload["error"].lower()
    session.execute.assert_not_called()


async def test_create_pir_executes_when_mutations_enabled(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"pirAdd": {"id": "pir--1", "name": "PIR A"}}

    result = await create_pir_tool.handle(session, {"name": "PIR A", "description": "Desc"})

    payload = json.loads(result[0].text)
    assert payload == {"success": True, "data": {"id": "pir--1", "name": "PIR A"}}
    assert session.execute.await_count == 1
    sent_input = session.execute.await_args.kwargs["variable_values"]["input"]
    assert sent_input["name"] == "PIR A"
    assert sent_input["pir_type"] == "THREAT_CUSTOM"
    assert sent_input["pir_rescan_days"] == 30
    assert sent_input["pir_criteria"][0]["weight"] == 1


async def test_create_case_rfi_executes_when_mutations_enabled(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"result": {"id": "case-rfi--1", "name": "RFI A"}}

    result = await create_case_rfi_tool.handle(session, {"name": "RFI A"})

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["id"] == "case-rfi--1"
    assert session.execute.await_count >= 1


async def test_add_objects_to_case_rfi_deduplicates_and_executes(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"result": {"id": "relation--1"}}

    result = await add_objects_to_case_rfi_tool.handle(
        session,
        {"id": "case-rfi--1", "object_ids": ["indicator--1", "malware--1", "indicator--1"]},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["case_rfi_id"] == "case-rfi--1"
    assert payload["data"]["added_object_ids"] == ["indicator--1", "malware--1"]
    assert session.execute.await_count == 2


async def test_add_objects_to_case_rfi_requires_non_empty_list(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()

    result = await add_objects_to_case_rfi_tool.handle(
        session,
        {"id": "case-rfi--1", "object_ids": []},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "object_ids" in payload["error"]
    session.execute.assert_not_called()


async def test_list_pirs_validates_first_range():
    session = AsyncMock()

    result = await list_pirs_tool.handle(session, {"first": 0})

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "first" in payload["error"]
    session.execute.assert_not_called()

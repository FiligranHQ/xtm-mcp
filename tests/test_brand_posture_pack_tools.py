from __future__ import annotations

import json
from unittest.mock import AsyncMock

from opencti_mcp.tools import create_external_reference as create_external_reference_tool
from opencti_mcp.tools import create_identity as create_identity_tool
from opencti_mcp.tools import list_stix_core_objects as list_stix_core_objects_tool


async def test_list_stix_core_objects_executes_with_types_and_search():
    session = AsyncMock()
    session.execute.return_value = {"stixCoreObjects": {"edges": [{"node": {"id": "report--1"}}]}}

    result = await list_stix_core_objects_tool.handle(
        session,
        {
            "types": ["Report", "Campaign"],
            "search": "brand",
            "first": 25,
        },
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["edges"][0]["node"]["id"] == "report--1"
    assert session.execute.await_args.kwargs["variable_values"]["types"] == ["Report", "Campaign"]
    assert session.execute.await_args.kwargs["variable_values"]["search"] == "brand"
    assert session.execute.await_args.kwargs["variable_values"]["first"] == 25


async def test_create_identity_uses_organization_add_for_organization(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"organizationAdd": {"id": "identity--1", "name": "Acme"}}

    result = await create_identity_tool.handle(
        session,
        {"name": "Acme", "type": "Organization"},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["id"] == "identity--1"
    assert session.execute.await_args.kwargs["variable_values"]["input"]["name"] == "Acme"


async def test_create_identity_uses_identity_add_for_non_organization(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()
    session.execute.return_value = {"identityAdd": {"id": "identity--2", "name": "Analyst User"}}

    result = await create_identity_tool.handle(
        session,
        {"name": "Analyst User", "type": "Individual"},
    )

    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["data"]["id"] == "identity--2"
    assert session.execute.await_args.kwargs["variable_values"]["input"]["type"] == "Individual"


async def test_create_external_reference_requires_source_or_url(monkeypatch):
    monkeypatch.setenv("OPENCTI_ENABLE_MUTATIONS", "true")
    session = AsyncMock()

    result = await create_external_reference_tool.handle(session, {})

    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "source_name or url is required" in payload["error"]
    session.execute.assert_not_called()

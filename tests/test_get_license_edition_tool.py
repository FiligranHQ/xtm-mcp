from __future__ import annotations

import json
from unittest.mock import AsyncMock

from opencti_mcp.tools import get_license_edition as get_license_edition_tool


async def test_get_license_edition_reports_ee_when_value_present():
    session = AsyncMock()
    session.execute.return_value = {"settings": {"enterprise_edition": "2026-01-15T00:00:00.000Z"}}

    result = await get_license_edition_tool.handle(session, {})
    payload = json.loads(result[0].text)

    assert payload["success"] is True
    assert payload["data"]["edition"] == "EE"
    assert payload["data"]["source_field"] == "enterprise_edition"


async def test_get_license_edition_reports_ce_when_value_is_null():
    session = AsyncMock()
    session.execute.return_value = {"settings": {"enterprise_edition": None}}

    result = await get_license_edition_tool.handle(session, {})
    payload = json.loads(result[0].text)

    assert payload["success"] is True
    assert payload["data"]["edition"] == "CE"
    assert payload["data"]["source_field"] == "enterprise_edition"


async def test_get_license_edition_uses_camel_case_fallback():
    session = AsyncMock()
    session.execute.side_effect = [
        Exception("Cannot query field 'enterprise_edition' on type 'Settings'."),
        {"settings": {"enterpriseEdition": "2026-01-15T00:00:00.000Z"}},
    ]

    result = await get_license_edition_tool.handle(session, {})
    payload = json.loads(result[0].text)

    assert payload["success"] is True
    assert payload["data"]["edition"] == "EE"
    assert payload["data"]["source_field"] == "enterpriseEdition"
    assert session.execute.await_count == 2


async def test_get_license_edition_returns_error_when_both_queries_fail():
    session = AsyncMock()
    session.execute.side_effect = [
        Exception("field enterprise_edition not found"),
        Exception("field enterpriseEdition not found"),
    ]

    result = await get_license_edition_tool.handle(session, {})
    payload = json.loads(result[0].text)

    assert payload["success"] is False
    assert "Unable to determine license edition" in payload["error"]

"""Helpers for write-operation gating."""

import os

_TRUE_VALUES = {"1", "true", "yes", "on"}


def mutations_enabled() -> bool:
    raw_value = os.getenv("OPENCTI_ENABLE_MUTATIONS", "").strip().lower()
    return raw_value in _TRUE_VALUES

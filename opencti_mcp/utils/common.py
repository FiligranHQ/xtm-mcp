"""Common helpers: URL utility and environment configuration."""

import os

from dotenv import load_dotenv


def read_opencti_env(strict: bool = False) -> tuple[str, str]:
    """Read OPENCTI_URL and OPENCTI_TOKEN from environment or .env.

    If ``strict`` is True, raises RuntimeError when either value is missing.
    Otherwise returns empty strings for missing values.
    """
    url = os.environ.get("OPENCTI_URL", "").strip()
    token = os.environ.get("OPENCTI_TOKEN", "").strip()
    if not url or not token:
        load_dotenv()
        url = os.environ.get("OPENCTI_URL", "").strip() or url
        token = os.environ.get("OPENCTI_TOKEN", "").strip() or token
    if strict:
        if not url:
            raise RuntimeError("OPENCTI_URL is required (set env var or in .env)")
        if not token:
            raise RuntimeError("OPENCTI_TOKEN is required (set env var or in .env)")
    return url, token

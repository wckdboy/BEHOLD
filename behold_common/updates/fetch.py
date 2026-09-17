# SPDX-License-Identifier: GPL-3.0-or-later
"""GitHub Releases HTTP helpers. Injectable urlopen — no bpy."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .core import (
    MAX_ZIP_BYTES,
    RELEASES_API,
    github_headers,
    is_allowed_download_url,
    parse_release_payload,
)

UrlOpen = Callable[..., Any]

_CHECK_TIMEOUT = 8.0
_DOWNLOAD_TIMEOUT = 60.0


def fetch_latest_release(
    *,
    urlopen: UrlOpen | None = None,
    timeout: float = _CHECK_TIMEOUT,
) -> dict[str, Any]:
    """GET ``/releases/latest``. Public API only — no token is sent."""
    opener = urlopen or urllib.request.urlopen
    request = urllib.request.Request(RELEASES_API, headers=github_headers())
    try:
        with opener(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise ValueError("GitHub rate limit") from exc
        raise ValueError(f"GitHub HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"GitHub request failed: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("GitHub response was not JSON") from exc
    parsed = parse_release_payload(data)
    if not parsed["stable"]:
        raise ValueError("latest GitHub release is not a stable tag")
    if parsed["version"] is None:
        raise ValueError("latest GitHub release tag is not a version")
    return parsed


def download_release_zip(
    url: str,
    dest: str,
    *,
    urlopen: UrlOpen | None = None,
    timeout: float = _DOWNLOAD_TIMEOUT,
) -> str:
    """Download a ``behold-*.zip`` from a GitHub release asset URL."""
    if not is_allowed_download_url(url):
        raise ValueError("refusing to download from a non-GitHub host")
    opener = urlopen or urllib.request.urlopen
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with opener(request, timeout=timeout) as response:
            length = _content_length(response)
            if length is not None and length > MAX_ZIP_BYTES:
                raise ValueError("release zip is larger than the safety limit")
            data = response.read(MAX_ZIP_BYTES + 1)
    except urllib.error.URLError as exc:
        raise ValueError(f"download failed: {exc}") from exc
    if len(data) > MAX_ZIP_BYTES:
        raise ValueError("release zip is larger than the safety limit")
    if not data.startswith(b"PK"):
        raise ValueError("download was not a zip")
    path = Path(dest)
    path.write_bytes(data)
    return str(path)


def _content_length(response: Any) -> int | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    raw = None
    try:
        raw = headers.get("Content-Length")
    except Exception:  # noqa: BLE001 — urllib header objects vary
        return None
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None

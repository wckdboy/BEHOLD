# SPDX-License-Identifier: GPL-3.0-or-later
"""Semver compare + GitHub release JSON parse. No network, no bpy."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Iterable, Literal, Mapping, Never
from urllib.parse import urlparse

from ..brand import DOCS_URL, RELEASES_URL, VERSION

GITHUB_OWNER = "wckdboy"
GITHUB_REPO = "BEHOLD"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = RELEASES_URL
USER_AGENT = f"BEHOLD-updater ({DOCS_URL})"
ZIP_NAME_RE = re.compile(r"^behold-.+\.zip$", re.IGNORECASE)
MAX_ZIP_BYTES = 50 * 1024 * 1024
ALLOWED_DOWNLOAD_HOSTS = frozenset(
    {
        "github.com",
        "api.github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
        "github-releases.githubusercontent.com",
    }
)

EXTENSIONS_INSTALL_OP = "extensions.package_install_files"
ADDON_INSTALL_OP = "preferences.addon_install"
ADDON_ENABLE_OP = "preferences.addon_enable"
USER_EXTENSIONS_REPO = "user_default"
RESTART_MESSAGE = "Restart Blender to finish the update."

FailureStage = Literal["check", "download", "install", "no_zip"]
FailureKind = Literal["network", "github", "download", "install", "no_zip"]


def installed_version() -> tuple[int, ...]:
    return tuple(VERSION)


def version_string(version: tuple[int, ...] | None = None) -> str:
    value = installed_version() if version is None else version
    if not value:
        return "?"
    return ".".join(str(part) for part in value)


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """``v0.10.0`` / ``0.10`` → ``(0, 10, 0)`` / ``(0, 10)``.

    Stops at the first non-numeric component, so ``v0.10.0-rc.1`` still
    compares as ``(0, 10, 0)``. Draft / prerelease flags are handled separately.
    """
    if not text:
        return None
    cleaned = str(text).strip().lstrip("vV")
    parts: list[int] = []
    for chunk in cleaned.replace("-", ".").replace("_", ".").split("."):
        if not chunk.isdigit():
            break
        parts.append(int(chunk))
    return tuple(parts) if parts else None


def is_newer(
    latest: tuple[int, ...] | None,
    current: tuple[int, ...] | None,
) -> bool:
    """True when ``latest`` is strictly newer. ``(0, 10)`` equals ``(0, 10, 0)``."""
    if not latest or not current:
        return False
    width = max(len(latest), len(current))
    return _pad(latest, width) > _pad(current, width)


def github_headers() -> dict[str, str]:
    """Public GitHub API headers. Never attach a token."""
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def is_allowed_download_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = parsed.netloc.lower()
    if host in ALLOWED_DOWNLOAD_HOSTS:
        return True
    return host.endswith(".githubusercontent.com")


def is_behold_zip_name(name: str) -> bool:
    return bool(name) and ZIP_NAME_RE.match(name) is not None


def pick_zip_asset(
    assets: Iterable[Mapping[str, Any]] | None,
    *,
    tag: str = "",
) -> dict[str, str] | None:
    """Prefer ``behold-<version>.zip``; ignore GitHub source zipballs."""
    zips: list[dict[str, str]] = []
    for asset in assets or ():
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if not is_behold_zip_name(name) or not url:
            continue
        zips.append({"name": name, "url": url})
    if not zips:
        return None
    wanted = version_string(parse_version(tag)) if tag else ""
    if wanted and wanted != "?":
        needle = f"behold-{wanted}.zip"
        for item in zips:
            if item["name"].lower() == needle:
                return item
    return zips[0]


def parse_release_payload(data: Any) -> dict[str, Any]:
    """Normalize a GitHub Releases API object. Does not touch the network."""
    if not isinstance(data, dict):
        raise ValueError("GitHub release payload must be an object")
    message = data.get("message")
    if "tag_name" not in data:
        raise ValueError(str(message) if message else "unexpected GitHub payload")
    tag = str(data.get("tag_name") or "")
    html_url = str(data.get("html_url") or "") or RELEASES_PAGE
    stable = not bool(data.get("draft")) and not bool(data.get("prerelease"))
    version = parse_version(tag)
    asset = pick_zip_asset(data.get("assets") or (), tag=tag)
    return {
        "stable": stable,
        "tag": tag,
        "version": version,
        "html_url": html_url,
        "zip_name": asset["name"] if asset else "",
        "zip_url": asset["url"] if asset else "",
    }


def parse_release_json(text: str) -> dict[str, Any]:
    return parse_release_payload(json.loads(text))


def should_auto_check(
    enabled: bool,
    last_iso: str,
    today: date | None = None,
) -> bool:
    """At most one automatic GitHub check per calendar day."""
    if not enabled:
        return False
    if not last_iso:
        return True
    when = today or date.today()
    try:
        year, month, day = (int(part) for part in last_iso.split("-")[:3])
        return when > date(year, month, day)
    except (ValueError, TypeError):
        return True


def available_from_cache(
    latest_tag: str,
    *,
    installed: tuple[int, ...] | None = None,
    html_url: str = "",
    zip_url: str = "",
) -> dict[str, str] | None:
    latest = parse_version(latest_tag)
    current = installed if installed is not None else installed_version()
    if not is_newer(latest, current):
        return None
    return {
        "version": version_string(latest),
        "tag": latest_tag,
        "url": html_url or RELEASES_PAGE,
        "zip_url": zip_url if is_allowed_download_url(zip_url) else "",
    }


def describe_failure(stage: FailureStage, error: str = "") -> dict[str, str]:
    """Artist-facing what-failed + next step. Always points at Open release."""
    lowered = error.lower()
    if stage == "check":
        if "rate limit" in lowered:
            return {
                "kind": "github",
                "line": "GitHub rate limit — try again in a bit",
                "detail": "Or Open release and download the zip yourself.",
            }
        if "not a stable" in lowered or "not a version" in lowered:
            return {
                "kind": "github",
                "line": "GitHub has no usable stable release yet",
                "detail": "Open release and install a zip from there.",
            }
        return {
            "kind": "network",
            "line": "Could not reach GitHub",
            "detail": "Check your network, then Check for updates. Or Open release.",
        }
    if stage == "download":
        return {
            "kind": "download",
            "line": "Could not download the update zip",
            "detail": "Check your network, then Install again. Or Open release.",
        }
    if stage == "install":
        return {
            "kind": "install",
            "line": "Install from Disk failed",
            "detail": "Open release, download behold-*.zip, then Preferences → Install from Disk.",
        }
    if stage == "no_zip":
        return {
            "kind": "no_zip",
            "line": "This release has no behold-*.zip",
            "detail": "Open release and install the zip the same way as the first time.",
        }
    unreachable: Never = stage
    raise RuntimeError(f"unhandled update failure stage: {unreachable}")


def infer_failure_stage(kind: str, error: str = "") -> FailureStage:
    """Map stored prefs kind / leftover error text back to a failure stage."""
    if kind == "download":
        return "download"
    if kind == "install":
        return "install"
    if kind == "no_zip":
        return "no_zip"
    if kind in {"network", "github", "check"}:
        return "check"
    text = error.lower()
    if "behold-*.zip" in text or "no behold" in text:
        return "no_zip"
    if "install from disk" in text or "install failed" in text:
        return "install"
    if "download" in text:
        return "download"
    return "check"


def failure_copy(*, kind: str = "", error: str = "") -> dict[str, str]:
    return describe_failure(infer_failure_stage(kind, error), error)


def cache_from_parsed(
    parsed: Mapping[str, Any],
    *,
    today: date | None = None,
    error: str = "",
    stage: FailureStage = "check",
) -> dict[str, str]:
    when = (today or date.today()).isoformat()
    if error:
        copy = describe_failure(stage, error)
        return {
            "update_last_check": when,
            "update_last_error": copy["line"],
            "update_error_kind": copy["kind"],
        }
    if not parsed.get("stable"):
        copy = describe_failure("check", "latest GitHub release is not a stable tag")
        return {
            "update_last_check": when,
            "update_last_error": copy["line"],
            "update_error_kind": copy["kind"],
        }
    return {
        "update_last_check": when,
        "update_latest_tag": str(parsed.get("tag") or ""),
        "update_latest_url": str(parsed.get("html_url") or RELEASES_PAGE),
        "update_latest_zip_url": str(parsed.get("zip_url") or ""),
        "update_last_error": "",
        "update_error_kind": "",
    }


def prefs_status_copy(
    *,
    checking: bool,
    installing: bool,
    last_iso: str,
    error: str,
    available: Mapping[str, str] | None,
    installed: tuple[int, ...] | None = None,
    error_kind: str = "",
) -> dict[str, str]:
    current = version_string(installed)
    if checking:
        return {"line": "Checking GitHub…", "detail": "", "alert": ""}
    if installing:
        return {
            "line": "Installing update…",
            "detail": RESTART_MESSAGE,
            "alert": "",
        }
    if error:
        copy = failure_copy(kind=error_kind, error=error)
        return {
            "line": copy["line"],
            "detail": copy["detail"],
            "alert": "ERROR",
        }
    if available:
        return {
            "line": f"Update available: {available['version']}",
            "detail": last_iso and f"Last checked: {last_iso}" or "",
            "alert": "",
        }
    if not last_iso:
        return {"line": "Not checked yet", "detail": "", "alert": ""}
    return {
        "line": f"BEHOLD {current} is up to date",
        "detail": f"Last checked: {last_iso}",
        "alert": "",
    }


def extensions_install_kwargs(
    filepath: str,
    known_props: frozenset[str] | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "filepath": filepath,
        "repo": USER_EXTENSIONS_REPO,
        "enable_on_install": True,
        "overwrite": True,
    }
    return _filter_kwargs(kwargs, known_props)


def addon_install_kwargs(
    filepath: str,
    known_props: frozenset[str] | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "filepath": filepath,
        "overwrite": True,
    }
    return _filter_kwargs(kwargs, known_props)


def pick_install_operator(available_ops: Iterable[str]) -> str | None:
    names = set(available_ops)
    if EXTENSIONS_INSTALL_OP in names:
        return EXTENSIONS_INSTALL_OP
    if ADDON_INSTALL_OP in names:
        return ADDON_INSTALL_OP
    return None


def _pad(version: tuple[int, ...], width: int) -> tuple[int, ...]:
    return version + (0,) * (width - len(version))


def _filter_kwargs(
    kwargs: dict[str, Any],
    known_props: frozenset[str] | None,
) -> dict[str, Any]:
    if known_props is None:
        return kwargs
    return {key: value for key, value in kwargs.items() if key in known_props}

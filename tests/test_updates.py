# SPDX-License-Identifier: GPL-3.0-or-later
"""GitHub version check / release parse / install wiring — no live network."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from tests.support import ROOT, load_addon_module, load_module

core = load_addon_module("behold/updates/core.py", "behold.updates.core")
fetch = load_addon_module("behold/updates/fetch.py", "behold.updates.fetch")
brand = load_module("behold/brand.py", "behold.brand")

FIXTURES = ROOT / "tests" / "fixtures" / "github"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}

    def read(self, size: int | None = None) -> bytes:
        if size is None:
            return self._payload
        return self._payload[:size]

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        del args
        return False


class VersionCompareTests(unittest.TestCase):
    def test_parse_version_strips_v_and_stops_at_prerelease(self) -> None:
        self.assertEqual(core.parse_version("v0.10.0"), (0, 10, 0))
        self.assertEqual(core.parse_version("0.9"), (0, 9))
        self.assertEqual(core.parse_version("v0.11.0-rc.1"), (0, 11, 0))
        self.assertIsNone(core.parse_version(""))
        self.assertIsNone(core.parse_version("latest"))

    def test_is_newer_pads_missing_patch(self) -> None:
        self.assertTrue(core.is_newer((0, 10, 0), (0, 9, 0)))
        self.assertTrue(core.is_newer((0, 10), (0, 9, 9)))
        self.assertFalse(core.is_newer((0, 10), (0, 10, 0)))
        self.assertFalse(core.is_newer((0, 9, 0), (0, 10, 0)))
        self.assertFalse(core.is_newer(None, (0, 10, 0)))
        self.assertFalse(core.is_newer((0, 10, 0), None))

    def test_installed_version_matches_brand(self) -> None:
        self.assertEqual(brand.VERSION, (0, 11, 0))
        self.assertEqual(core.installed_version(), (0, 11, 0))
        self.assertEqual(core.version_string(), "0.11.0")


class ReleaseParseTests(unittest.TestCase):
    def test_latest_stable_fixture_picks_behold_zip(self) -> None:
        parsed = core.parse_release_payload(_load_json("latest_stable.json"))
        self.assertTrue(parsed["stable"])
        self.assertEqual(parsed["tag"], "v0.10.0")
        self.assertEqual(parsed["version"], (0, 10, 0))
        self.assertEqual(parsed["zip_name"], "behold-0.10.0.zip")
        self.assertTrue(parsed["zip_url"].endswith("/behold-0.10.0.zip"))
        self.assertNotIn("zipball", parsed["zip_url"])

    def test_json_helper_reads_fixture_file(self) -> None:
        text = (FIXTURES / "current_stable.json").read_text(encoding="utf-8")
        parsed = core.parse_release_json(text)
        self.assertEqual(parsed["tag"], "v0.9.0")
        self.assertEqual(parsed["zip_name"], "behold-0.9.0.zip")

    def test_prerelease_is_not_stable(self) -> None:
        parsed = core.parse_release_payload(_load_json("prerelease.json"))
        self.assertFalse(parsed["stable"])
        self.assertEqual(parsed["version"], (0, 11, 0))

    def test_no_zip_asset_leaves_url_empty(self) -> None:
        parsed = core.parse_release_payload(_load_json("no_zip_asset.json"))
        self.assertEqual(parsed["zip_name"], "")
        self.assertEqual(parsed["zip_url"], "")
        self.assertTrue(parsed["html_url"].endswith("/v0.10.0"))

    def test_rate_limit_payload_raises(self) -> None:
        with self.assertRaises(ValueError):
            core.parse_release_payload(_load_json("rate_limit.json"))

    def test_zipball_and_source_names_are_ignored(self) -> None:
        parsed = core.parse_release_payload(
            {
                "tag_name": "v0.10.0",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/wckdboy/BEHOLD/releases/tag/v0.10.0",
                "zipball_url": "https://api.github.com/repos/wckdboy/BEHOLD/zipball/v0.10.0",
                "assets": [
                    {
                        "name": "Source code.zip",
                        "browser_download_url": "https://github.com/wckdboy/BEHOLD/archive/refs/tags/v0.10.0.zip",
                    },
                    {
                        "name": "behold-0.10.0.zip",
                        "browser_download_url": "https://github.com/wckdboy/BEHOLD/releases/download/v0.10.0/behold-0.10.0.zip",
                    },
                ],
            }
        )
        self.assertEqual(parsed["zip_name"], "behold-0.10.0.zip")


class CacheAndScheduleTests(unittest.TestCase):
    def test_available_from_cache_when_newer(self) -> None:
        update = core.available_from_cache(
            "v0.11.0",
            installed=(0, 10, 0),
            html_url="https://github.com/wckdboy/BEHOLD/releases/tag/v0.11.0",
            zip_url="https://github.com/wckdboy/BEHOLD/releases/download/v0.11.0/behold-0.11.0.zip",
        )
        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["version"], "0.11.0")
        self.assertTrue(update["zip_url"].endswith("behold-0.11.0.zip"))

    def test_available_from_cache_when_current_or_older(self) -> None:
        self.assertIsNone(
            core.available_from_cache("v0.10.0", installed=(0, 10, 0))
        )
        self.assertIsNone(
            core.available_from_cache("v0.9.0", installed=(0, 10, 0))
        )

    def test_rejects_non_github_zip_url(self) -> None:
        update = core.available_from_cache(
            "v0.11.0",
            installed=(0, 10, 0),
            zip_url="https://evil.example/behold.zip",
        )
        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["zip_url"], "")

    def test_should_auto_check_once_per_day(self) -> None:
        today = date(2026, 9, 14)
        self.assertTrue(core.should_auto_check(True, "", today))
        self.assertFalse(core.should_auto_check(True, "2026-09-14", today))
        self.assertTrue(core.should_auto_check(True, "2026-09-13", today))
        self.assertFalse(core.should_auto_check(False, "", today))
        self.assertTrue(core.should_auto_check(True, "not-a-date", today))

    def test_status_copy_covers_states(self) -> None:
        checking = core.prefs_status_copy(
            checking=True,
            installing=False,
            last_iso="",
            error="",
            available=None,
        )
        self.assertEqual(checking["line"], "Checking GitHub…")
        available = core.prefs_status_copy(
            checking=False,
            installing=False,
            last_iso="2026-09-14",
            error="",
            available={"version": "0.11.0"},
            installed=(0, 10, 0),
        )
        self.assertEqual(available["line"], "Update available: 0.11.0")
        current = core.prefs_status_copy(
            checking=False,
            installing=False,
            last_iso="2026-09-14",
            error="",
            available=None,
            installed=(0, 10, 0),
        )
        self.assertIn("0.10.0 is up to date", current["line"])
        network = core.prefs_status_copy(
            checking=False,
            installing=False,
            last_iso="2026-09-14",
            error="GitHub request failed: timed out",
            error_kind="network",
            available=None,
        )
        self.assertEqual(network["line"], "Could not reach GitHub")
        self.assertIn("network", network["detail"].lower())
        self.assertIn("Open release", network["detail"])
        self.assertEqual(network["alert"], "ERROR")
        self.assertNotIn("Try again later", network["detail"])
        install = core.prefs_status_copy(
            checking=False,
            installing=False,
            last_iso="2026-09-14",
            error="Install failed: Repository not set",
            error_kind="install",
            available={"version": "0.11.0"},
        )
        self.assertEqual(install["line"], "Install from Disk failed")
        self.assertIn("Open release", install["detail"])
        self.assertIn("Install from Disk", install["detail"])


class FailureCopyTests(unittest.TestCase):
    def test_every_stage_names_what_failed_and_open_release(self) -> None:
        stages = ("check", "download", "install", "no_zip")
        for stage in stages:
            copy = core.describe_failure(stage, "GitHub request failed")
            self.assertTrue(copy["line"], msg=stage)
            self.assertIn("Open release", copy["detail"], msg=stage)

    def test_rate_limit_and_missing_zip_are_specific(self) -> None:
        rate = core.describe_failure("check", "GitHub rate limit")
        self.assertIn("rate limit", rate["line"].lower())
        self.assertIn("Open release", rate["detail"])
        missing = core.describe_failure("no_zip")
        self.assertIn("behold-*.zip", missing["line"])
        self.assertIn("Open release", missing["detail"])

    def test_infer_stage_from_stored_kind_or_text(self) -> None:
        self.assertEqual(core.infer_failure_stage("install", ""), "install")
        self.assertEqual(core.infer_failure_stage("", "download failed: timeout"), "download")
        self.assertEqual(core.infer_failure_stage("", "no behold-*.zip"), "no_zip")
        copy = core.failure_copy(kind="network", error="Could not reach GitHub")
        self.assertIn("network", copy["detail"].lower())


class FetchInjectTests(unittest.TestCase):
    def test_headers_are_public_and_have_no_token(self) -> None:
        headers = core.github_headers()
        self.assertNotIn("Authorization", headers)
        self.assertTrue(all("token" not in value.lower() for value in headers.values()))
        self.assertIn("BEHOLD-updater", headers["User-Agent"])
        self.assertEqual(headers["Accept"], "application/vnd.github+json")

    def test_fetch_latest_release_uses_fixture_json(self) -> None:
        payload = json.dumps(_load_json("latest_stable.json")).encode("utf-8")
        captured: dict[str, object] = {}

        def urlopen(request: object, timeout: float = 0.0) -> FakeResponse:
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(payload)

        parsed = fetch.fetch_latest_release(urlopen=urlopen, timeout=3.0)
        self.assertEqual(parsed["tag"], "v0.10.0")
        self.assertEqual(captured["timeout"], 3.0)
        headers = getattr(captured["request"], "headers", {})
        header_text = " ".join(str(item) for item in headers)
        self.assertNotIn("Authorization", header_text)
        self.assertNotIn("token", header_text.lower())

    def test_fetch_rejects_prerelease_fixture(self) -> None:
        payload = json.dumps(_load_json("prerelease.json")).encode("utf-8")

        def urlopen(request: object, timeout: float = 0.0) -> FakeResponse:
            del request, timeout
            return FakeResponse(payload)

        with self.assertRaises(ValueError):
            fetch.fetch_latest_release(urlopen=urlopen)

    def test_download_release_zip_writes_bytes(self) -> None:
        dest = Path("/tmp/behold-update-test.zip")
        if dest.exists():
            dest.unlink()
        zip_bytes = b"PK\x03\x04" + b"fake-zip"

        def urlopen(request: object, timeout: float = 0.0) -> FakeResponse:
            del timeout
            full = getattr(request, "full_url", "") or request.get_full_url()  # type: ignore[attr-defined]
            self.assertIn("github.com/wckdboy/BEHOLD/releases/download", full)
            return FakeResponse(zip_bytes, headers={"Content-Length": str(len(zip_bytes))})

        url = "https://github.com/wckdboy/BEHOLD/releases/download/v0.10.0/behold-0.10.0.zip"
        path = fetch.download_release_zip(url, str(dest), urlopen=urlopen)
        self.assertEqual(Path(path).read_bytes(), zip_bytes)
        dest.unlink()

    def test_download_rejects_non_github_host(self) -> None:
        with self.assertRaises(ValueError):
            fetch.download_release_zip(
                "https://example.com/behold-0.10.0.zip",
                "/tmp/nope.zip",
            )


class InstallKwargsTests(unittest.TestCase):
    def test_extensions_install_kwargs_for_5_2(self) -> None:
        kwargs = core.extensions_install_kwargs("/tmp/behold-0.10.0.zip")
        self.assertEqual(kwargs["filepath"], "/tmp/behold-0.10.0.zip")
        self.assertEqual(kwargs["repo"], "user_default")
        self.assertTrue(kwargs["enable_on_install"])
        self.assertTrue(kwargs["overwrite"])
        stripped = core.extensions_install_kwargs(
            "/tmp/behold-0.10.0.zip",
            known_props=frozenset({"filepath", "overwrite"}),
        )
        self.assertEqual(set(stripped), {"filepath", "overwrite"})

    def test_pick_install_operator_prefers_extensions(self) -> None:
        self.assertEqual(
            core.pick_install_operator(
                ("preferences.addon_install", "extensions.package_install_files")
            ),
            "extensions.package_install_files",
        )
        self.assertEqual(
            core.pick_install_operator(("preferences.addon_install",)),
            "preferences.addon_install",
        )
        self.assertIsNone(core.pick_install_operator(("wm.url_open",)))


class WiringTests(unittest.TestCase):
    def test_operators_and_prefs_are_wired(self) -> None:
        operators = (ROOT / "behold" / "updates" / "operators.py").read_text(
            encoding="utf-8"
        )
        runtime = (ROOT / "behold" / "updates" / "runtime.py").read_text(
            encoding="utf-8"
        )
        prefs = (ROOT / "behold" / "preferences.py").read_text(encoding="utf-8")
        panels = (ROOT / "behold" / "ui" / "panels.py").read_text(encoding="utf-8")
        chrome = (ROOT / "behold" / "ui" / "chrome.py").read_text(encoding="utf-8")
        init = (ROOT / "behold" / "__init__.py").read_text(encoding="utf-8")
        manifest = (ROOT / "behold" / "blender_manifest.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn('bl_idname = "behold.check_updates"', operators)
        self.assertIn('bl_idname = "behold.install_update"', operators)
        self.assertIn('bl_idname = "behold.open_release"', operators)
        self.assertIn('bl_idname = "behold.dismiss_update"', operators)
        self.assertIn("request_check(force=True)", operators)
        self.assertIn("daemon=True", runtime)
        self.assertIn("bpy.app.timers.register", runtime)
        self.assertIn("check_for_updates", prefs)
        self.assertIn("default=True", prefs)
        self.assertIn("behold.check_updates", prefs)
        self.assertIn("behold.install_update", prefs)
        self.assertIn("behold.open_release", prefs)
        self.assertIn("update_error_kind", prefs)
        self.assertIn("alert", prefs)
        self.assertIn("draw_update_notice", panels)
        self.assertIn("behold.open_release", chrome)
        self.assertIn("behold.check_updates", chrome)
        self.assertIn('icon="ERROR"', chrome)
        self.assertIn("Check again", chrome)
        self.assertIn("updates", init)
        self.assertIn("GitHub", manifest)
        self.assertNotIn("GITHUB_TOKEN", operators)
        self.assertNotIn("GITHUB_TOKEN", runtime)
        fetch_src = (ROOT / "behold" / "updates" / "fetch.py").read_text(encoding="utf-8")
        self.assertNotIn("GITHUB_TOKEN", fetch_src)
        self.assertNotIn("Bearer", fetch_src)
        self.assertNotIn("headers[\"Authorization\"]", fetch_src)

    def test_install_path_uses_5_2_extensions_then_addon_install(self) -> None:
        install = (ROOT / "behold" / "updates" / "blender_install.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("extensions.package_install_files", install)
        self.assertIn("preferences.addon_install", install)
        self.assertIn("user_default", install)
        self.assertIn("RESTART_MESSAGE", install)
        self.assertIn("restart is always required", install)
        self.assertIn("EXEC_DEFAULT", install)


if __name__ == "__main__":
    unittest.main()

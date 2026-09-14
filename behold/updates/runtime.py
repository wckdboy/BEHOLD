# SPDX-License-Identifier: GPL-3.0-or-later
"""Background GitHub check + zip download. bpy timers on the main thread only."""

from __future__ import annotations

import os
import tempfile
import threading
from datetime import date
from typing import Any

try:
    import bpy
except ImportError:
    bpy = None

from ..preferences import get_prefs
from . import blender_install
from . import fetch
from .core import (
    FailureStage,
    cache_from_parsed,
    describe_failure,
    should_auto_check,
)

_CHECK_DELAY = 6.0
_POLL = 0.4

_timer_running = False
_force_check = False
_check_thread: threading.Thread | None = None
_check_result: dict[str, Any] | None = None
_install_thread: threading.Thread | None = None
_install_result: dict[str, Any] | None = None
_install_requested = False
_dismissed = False
_lock = threading.Lock()


def is_checking() -> bool:
    thread = _check_thread
    return thread is not None and thread.is_alive()


def is_installing() -> bool:
    thread = _install_thread
    return thread is not None and thread.is_alive()


def notice_is_dismissed() -> bool:
    return _dismissed


def dismiss_notice() -> None:
    global _dismissed
    _dismissed = True


def reset_session() -> None:
    """Tests / unregister: drop session flags. Does not join worker threads."""
    global _timer_running, _force_check, _check_thread, _check_result
    global _install_thread, _install_result, _install_requested, _dismissed
    _timer_running = False
    _force_check = False
    _check_thread = None
    _check_result = None
    _install_thread = None
    _install_result = None
    _install_requested = False
    _dismissed = False


def start(delay: float = _CHECK_DELAY) -> None:
    """Schedule the daily check after register(). Delay keeps startup free."""
    global _timer_running
    if bpy is None or _timer_running:
        return
    _timer_running = True
    try:
        bpy.app.timers.register(_tick, first_interval=delay, persistent=True)
    except Exception as exc:  # noqa: BLE001
        _timer_running = False
        print("BEHOLD: update check not scheduled:", exc)


def stop() -> None:
    """Cancel-safe: stop the timer. Daemon workers are left to finish/exit."""
    global _timer_running, _force_check, _install_requested
    _timer_running = False
    _force_check = False
    _install_requested = False
    if bpy is None:
        return
    try:
        if bpy.app.timers.is_registered(_tick):
            bpy.app.timers.unregister(_tick)
    except Exception:  # noqa: BLE001
        pass


def request_check(*, force: bool = False) -> None:
    global _force_check
    if force:
        _force_check = True
    start(delay=0.15 if force else _CHECK_DELAY)


def request_install() -> None:
    global _install_requested
    _install_requested = True
    start(delay=0.15)


def _prefs():
    if bpy is None:
        return None
    try:
        return get_prefs(bpy.context)
    except Exception:  # noqa: BLE001
        return None


def _write_checking(prefs, value: bool) -> None:
    try:
        prefs.update_checking = value
    except Exception:  # noqa: BLE001
        pass


def _write_installing(prefs, value: bool) -> None:
    try:
        prefs.update_installing = value
    except Exception:  # noqa: BLE001
        pass


def _apply_check(prefs, result: dict[str, Any]) -> None:
    payload = cache_from_parsed(
        result.get("parsed") or {},
        today=date.today(),
        error=str(result.get("error") or ""),
        stage="check",
    )
    for key, value in payload.items():
        try:
            setattr(prefs, key, value)
        except Exception as exc:  # noqa: BLE001
            print("BEHOLD: could not store update check:", exc)
    _write_checking(prefs, False)


def _worker_check() -> None:
    global _check_result
    try:
        parsed = fetch.fetch_latest_release()
        payload: dict[str, Any] = {"parsed": parsed}
    except Exception as exc:  # noqa: BLE001 — never let a thread exception escape
        payload = {"error": str(exc)}
    with _lock:
        _check_result = payload


def _worker_install(url: str) -> None:
    global _install_result
    handle = None
    path = ""
    try:
        handle, path = tempfile.mkstemp(prefix="behold-update-", suffix=".zip")
        os.close(handle)
        handle = None
        fetch.download_release_zip(url, path)
        payload: dict[str, Any] = {"path": path}
    except Exception as exc:  # noqa: BLE001
        payload = {"error": str(exc), "path": path}
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass
    finally:
        if handle is not None:
            try:
                os.close(handle)
            except OSError:
                pass
    with _lock:
        _install_result = payload


def _start_check_thread() -> None:
    global _check_thread, _check_result, _force_check
    _check_result = None
    _force_check = False
    _check_thread = threading.Thread(target=_worker_check, daemon=True)
    _check_thread.start()


def _start_install_thread(url: str) -> None:
    global _install_thread, _install_result, _install_requested
    _install_result = None
    _install_requested = False
    _install_thread = threading.Thread(
        target=_worker_install,
        args=(url,),
        daemon=True,
    )
    _install_thread.start()


def _set_failure(prefs, stage: FailureStage, error: str = "") -> None:
    copy = describe_failure(stage, error)
    try:
        prefs.update_last_error = copy["line"]
        prefs.update_error_kind = copy["kind"]
    except Exception:  # noqa: BLE001
        pass
    print("BEHOLD:", copy["line"], copy["detail"])


def _finish_install(prefs, result: dict[str, Any]) -> None:
    _write_installing(prefs, False)
    path = str(result.get("path") or "")
    error = str(result.get("error") or "")
    if error:
        _set_failure(prefs, "download", error)
        return
    if not path:
        _set_failure(prefs, "download", "download produced no file")
        return
    try:
        installed = blender_install.install_zip_file(path)
        if not installed.get("ok"):
            _set_failure(
                prefs,
                "install",
                str(installed.get("message") or "install failed"),
            )
        else:
            try:
                prefs.update_last_error = ""
                prefs.update_error_kind = ""
            except Exception:  # noqa: BLE001
                pass
            print("BEHOLD:", installed.get("message"))
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _tick() -> float | None:
    """Main-thread timer: start workers, then apply results to preferences."""
    global _timer_running, _check_thread, _install_thread
    global _check_result, _install_result, _install_requested
    if bpy is None or not _timer_running:
        return None
    prefs = _prefs()
    if prefs is None:
        return _POLL

    with _lock:
        check_done = _check_result
        install_done = _install_result

    if _check_thread is not None and not _check_thread.is_alive() and check_done is not None:
        try:
            _apply_check(prefs, check_done)
        except Exception as exc:  # noqa: BLE001
            print("BEHOLD: could not apply update check:", exc)
        _check_thread = None
        with _lock:
            _check_result = None

    if _install_thread is not None and not _install_thread.is_alive() and install_done is not None:
        try:
            _finish_install(prefs, install_done)
        except Exception as exc:  # noqa: BLE001
            print("BEHOLD: could not apply update install:", exc)
        _install_thread = None
        with _lock:
            _install_result = None

    if is_checking() or is_installing():
        return _POLL

    if _install_requested:
        url = getattr(prefs, "update_latest_zip_url", "") or ""
        if not url:
            _install_requested = False
            _write_installing(prefs, False)
            _set_failure(prefs, "no_zip")
            return _POLL
        _write_installing(prefs, True)
        _start_install_thread(url)
        return _POLL

    want_check = _force_check or should_auto_check(
        bool(getattr(prefs, "check_for_updates", False)),
        str(getattr(prefs, "update_last_check", "") or ""),
    )
    if want_check and _check_thread is None:
        _write_checking(prefs, True)
        _start_check_thread()
        return _POLL

    if _force_check or _install_requested:
        return _POLL

    _timer_running = False
    return None

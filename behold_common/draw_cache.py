# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-redraw memo for N-panel draw. No Blender import.

Panel ``draw`` methods run many times while the mouse moves. CAD backend
status and scene product/studio flags do not need a fresh addon_utils /
``scene.objects`` walk on every sibling panel in the same pass.

Values live until ``clear()``. In Blender, ``draw_get`` arms a 0s timer so
the store drops after the current UI pass.
"""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")

CAD_STATUS_KEY = "cad_status"
SCENE_SNAP_KEY = "scene_snap"


class DrawOnceCache:
    """Key/value store for one UI pass (or until ``clear``)."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}
        self.reset_armed: bool = False

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        if key not in self._store:
            self._store[key] = factory()
        return self._store[key]  # type: ignore[return-value]

    def drop(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self.reset_armed = False

    def arm_reset(self, register: Callable[[Callable[[], None]], object]) -> bool:
        """Schedule ``clear`` after this pass. ``register`` is called once."""
        if self.reset_armed:
            return True

        def _reset() -> None:
            self.clear()

        try:
            register(_reset)
        except Exception:  # noqa: BLE001 — drawing must never fail the host
            return False
        self.reset_armed = True
        return True


def memo_by_fingerprint(
    store: dict[str, object],
    fingerprint: object,
    factory: Callable[[], T],
) -> T:
    """Reuse ``factory()`` while ``fingerprint`` is unchanged."""
    if store.get("fp") == fingerprint and "value" in store:
        return store["value"]  # type: ignore[return-value]
    value = factory()
    store.clear()
    store["fp"] = fingerprint
    store["value"] = value
    return value


DRAW = DrawOnceCache()


def _register_blender_timer(callback: Callable[[], None]) -> object:
    import bpy

    return bpy.app.timers.register(callback, first_interval=0.0)


def draw_get(key: str, factory: Callable[[], T]) -> T:
    """Return a per-pass value, arming a Blender timer to drop the store."""
    if not DRAW.arm_reset(_register_blender_timer):
        return factory()
    return DRAW.get_or_set(key, factory)


def invalidate_draw_key(key: str) -> None:
    DRAW.drop(key)

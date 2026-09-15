# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Utilities — feature-flagged CAD/build helpers (default off)."""

from __future__ import annotations

from .flag import (
    DEFAULT_ENABLE_UTILITIES,
    gated_ui_ids,
    show_utilities_panel,
)


def register() -> None:
    from . import registration as _registration

    _registration.register()


def unregister() -> None:
    from . import registration as _registration

    _registration.unregister()


def sync_registration(enabled: bool) -> None:
    from . import registration as _registration

    _registration.sync_registration(enabled)

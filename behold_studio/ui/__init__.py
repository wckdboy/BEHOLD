# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration for BEHOLD Studio."""

from . import panels


def register() -> None:
    panels.register()


def unregister() -> None:
    panels.unregister()

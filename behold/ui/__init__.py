# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration."""

from . import panels


def register() -> None:
    panels.register()


def unregister() -> None:
    panels.unregister()

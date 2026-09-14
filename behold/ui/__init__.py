# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration."""

from . import panels, pie


def register() -> None:
    panels.register()
    pie.register()


def unregister() -> None:
    pie.unregister()
    panels.unregister()

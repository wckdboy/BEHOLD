# SPDX-License-Identifier: GPL-3.0-or-later
"""CAD / STEP hybrid import package."""

from . import operators


def register() -> None:
    operators.register()


def unregister() -> None:
    operators.unregister()

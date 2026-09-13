# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified product file import (mesh + CAD)."""

from . import operators


def register() -> None:
    operators.register()


def unregister() -> None:
    operators.unregister()

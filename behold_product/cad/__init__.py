# SPDX-License-Identifier: GPL-3.0-or-later
"""CAD / STEP hybrid import package."""


def register() -> None:
    from . import operators

    operators.register()


def unregister() -> None:
    from . import operators

    operators.unregister()

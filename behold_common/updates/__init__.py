# SPDX-License-Identifier: GPL-3.0-or-later
"""Easy update: GitHub check, notice, one-click install from the release zip.

``register`` imports operators/runtime lazily so ``from .updates.core``
(used by preferences) does not pull bpy operators back into preferences.
"""


def register() -> None:
    from . import operators
    from . import runtime

    operators.register()
    runtime.start()


def unregister() -> None:
    from . import operators
    from . import runtime

    runtime.stop()
    operators.unregister()

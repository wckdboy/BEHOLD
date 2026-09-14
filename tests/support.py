# SPDX-License-Identifier: GPL-3.0-or-later
"""Load addon modules without executing behold/__init__.py (needs bpy)."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
UNIT_CUBE_STEP = ROOT / "tests" / "fixtures" / "unit_cube.step"


def load_module(relpath: str, name: str) -> ModuleType:
    path = ROOT / relpath
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _ensure_namespace(dotted: str) -> None:
    if dotted in sys.modules:
        return
    rel = Path(*dotted.split("."))
    module = types.ModuleType(dotted)
    module.__path__ = [str(ROOT / rel)]
    module.__package__ = dotted
    sys.modules[dotted] = module


def load_addon_module(relpath: str, dotted: str) -> ModuleType:
    """Load a bpy-free submodule so package-relative imports resolve.

    Does not execute ``behold/__init__.py`` (that module imports bpy).
    """
    parts = dotted.split(".")
    for index in range(1, len(parts)):
        _ensure_namespace(".".join(parts[:index]))
    return load_module(relpath, dotted)

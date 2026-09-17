# SPDX-License-Identifier: GPL-3.0-or-later
"""One-CTA empty-state spec — no Blender import."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmptyState:
    title: str
    hint: str
    operator: str
    operator_text: str
    icon: str

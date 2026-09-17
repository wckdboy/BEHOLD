# SPDX-License-Identifier: GPL-3.0-or-later
"""Native BEHOLD chrome primitives: hero, cards, section icons."""

from __future__ import annotations

from bpy.types import UILayout

from .brand import PRODUCT_CREDIT, PRODUCT_NAME
from .previews import draw_mark_label


def draw_hero(layout: UILayout, *, subtitle: str = "") -> None:
    box = layout.box()
    draw_mark_label(box, PRODUCT_NAME)
    box.label(text=PRODUCT_CREDIT)
    if subtitle:
        box.label(text=subtitle)


def draw_section_icon(layout: UILayout, icon: str) -> None:
    layout.label(text="", icon=icon)


def draw_parked_heading(
    layout: UILayout,
    text: str,
    icon: str,
    *,
    leading_separator: bool = True,
) -> None:
    if leading_separator:
        layout.separator()
    layout.label(text=text, icon=icon)


def draw_empty_card(
    layout: UILayout,
    spec=None,
    *,
    title: str = "",
    hint: str = "",
    operator: str = "",
    operator_text: str = "",
    icon: str = "INFO",
) -> UILayout:
    """One primary CTA. Callers may add a quieter secondary control on the box."""
    if spec is not None:
        title = spec.title
        hint = spec.hint
        operator = spec.operator
        operator_text = spec.operator_text
        icon = spec.icon
    box = layout.box()
    box.label(text=title, icon="INFO")
    if hint:
        box.label(text=hint)
    if operator:
        box.operator(operator, text=operator_text or title, icon=icon)
    return box

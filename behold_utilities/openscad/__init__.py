# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenSCAD export for the Danish wall stack — no Blender import."""

from __future__ import annotations

from pathlib import Path

from ..wall import WallSpec, m_to_mm

TEMPLATE_NAME = "wall_stack.scad"


def suggest_scad_path(blend_filepath: str) -> str:
    """Write beside the .blend when the file has been saved; else empty."""
    if not blend_filepath:
        return ""
    parent = Path(blend_filepath).expanduser().resolve().parent
    return str(parent / "behold_danish_wall.scad")


def generate_wall_stack_scad(spec: WallSpec) -> str:
    width = m_to_mm(spec.width_m)
    height = m_to_mm(spec.height_m)
    ext = spec.layers.exterior_mm
    ins = spec.layers.insulation_mm
    inn = spec.layers.interior_mm
    door_w = m_to_mm(spec.door_width_m)
    door_h = m_to_mm(spec.door_height_m)
    door = "true" if spec.include_door else "false"
    return (
        "// BEHOLD Utilities — Danish wall stack (millimetres)\n"
        "// Feature-flagged helper. Not structural engineering. MinAltan snit are reference only.\n"
        f"width = {width:.3f};\n"
        f"height = {height:.3f};\n"
        f"exterior = {ext:.3f};\n"
        f"insulation = {ins:.3f};\n"
        f"interior = {inn:.3f};\n"
        f"door = {door};\n"
        f"door_w = {door_w:.3f};\n"
        f"door_h = {door_h:.3f};\n"
        "\n"
        "module danish_wall() {\n"
        "    difference() {\n"
        "        union() {\n"
        '            color("firebrick") cube([width, exterior, height]);\n'
        "            translate([0, exterior, 0])\n"
        '                color("khaki") cube([width, insulation, height]);\n'
        "            translate([0, exterior + insulation, 0])\n"
        '                color("white") cube([width, interior, height]);\n'
        "        }\n"
        "        if (door) {\n"
        "            translate([(width - door_w) / 2, -1, 0])\n"
        "                cube([door_w, exterior + insulation + interior + 2, door_h]);\n"
        "        }\n"
        "    }\n"
        "}\n"
        "\n"
        "danish_wall();\n"
    )

# SPDX-License-Identifier: GPL-3.0-or-later
"""Built-in procedural PBR starter rack (no external textures)."""

from __future__ import annotations

from typing import Iterable

import bpy
from bpy.props import EnumProperty
from bpy.types import Context, Material, Object, Operator

from .presets import (
    EMPTY_NO_MESH,
    PRESETS,
    apply_preset_to_sockets,
    is_dressable_mesh_name,
    material_name_for,
    preset_enum_items,
)
from ..ui.messages import report_set


def dressable_meshes(objects: Iterable[Object]) -> list[Object]:
    return [
        obj
        for obj in objects
        if getattr(obj, "type", None) == "MESH" and is_dressable_mesh_name(obj.name)
    ]


def _principled_bsdf(mat: Material):
    nodes = mat.node_tree.nodes
    node = nodes.get("Principled BSDF")
    if node is not None:
        return node
    for candidate in nodes:
        if candidate.type == "BSDF_PRINCIPLED":
            return candidate
    return None


def _ensure_principled(mat: Material):
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = _principled_bsdf(mat)
    if bsdf is not None:
        return bsdf
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = next((node for node in tree.nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(bsdf.outputs[0], output.inputs[0])
    return bsdf


def _configure_surface_for_preset(mat: Material, preset: dict) -> None:
    """EEVEE / EEVEE Next refraction flags for glass. Missing attrs are skipped."""
    transmission = float(preset.get("transmission", 0.0) or 0.0)
    if transmission <= 0.0:
        return
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = "BLENDED"
        except TypeError:
            pass
        except ValueError:
            pass
    if hasattr(mat, "blend_method"):
        for mode in ("HASHED", "BLEND"):
            try:
                mat.blend_method = mode
                break
            except TypeError:
                continue
            except ValueError:
                continue
    if hasattr(mat, "use_screen_refraction"):
        mat.use_screen_refraction = True
    if hasattr(mat, "use_raytrace_refraction"):
        mat.use_raytrace_refraction = True
    if hasattr(mat, "use_transparency"):
        mat.use_transparency = True
    if hasattr(mat, "refraction_depth"):
        try:
            mat.refraction_depth = 0.005
        except TypeError:
            pass


def apply_preset_to_material(mat: Material, preset: dict) -> dict[str, str]:
    bsdf = _ensure_principled(mat)
    written = apply_preset_to_sockets(bsdf.inputs, preset)
    _configure_surface_for_preset(mat, preset)
    return written


def apply_to_objects(objects: list[Object], preset_id: str) -> int:
    preset = PRESETS[preset_id]
    mat_name = material_name_for(preset_id)
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    apply_preset_to_material(mat, preset)
    count = 0
    for obj in dressable_meshes(objects):
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        count += 1
    return count


class BEHOLD_OT_apply_local_material(Operator):
    bl_idname = "behold.apply_local_material"
    bl_label = "Apply Local Material"
    bl_description = "Assign a built-in product PBR look to selected meshes"
    bl_options = {"REGISTER", "UNDO"}

    preset: EnumProperty(
        name="Preset",
        items=preset_enum_items(),
        default="METAL",
    )

    def execute(self, context: Context):
        targets = dressable_meshes(context.selected_objects)
        if not targets:
            self.report(report_set(EMPTY_NO_MESH), EMPTY_NO_MESH)
            return {"CANCELLED"}
        count = apply_to_objects(targets, self.preset)
        self.report(
            {"INFO"},
            f"Applied {PRESETS[self.preset]['label']} to {count} object(s)",
        )
        return {"FINISHED"}


CLASSES = (BEHOLD_OT_apply_local_material,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

# SPDX-License-Identifier: GPL-3.0-or-later
"""Built-in procedural PBR starter rack (no external textures)."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty
from bpy.types import Context, Operator


PRESETS: dict[str, dict] = {
    "METAL": {
        "label": "Metal",
        "base_color": (0.58, 0.58, 0.6, 1.0),
        "metallic": 1.0,
        "roughness": 0.25,
        "ior": 1.45,
    },
    "PLASTIC": {
        "label": "Plastic",
        "base_color": (0.12, 0.35, 0.75, 1.0),
        "metallic": 0.0,
        "roughness": 0.35,
        "ior": 1.45,
    },
    "RUBBER": {
        "label": "Rubber",
        "base_color": (0.05, 0.05, 0.05, 1.0),
        "metallic": 0.0,
        "roughness": 0.7,
        "ior": 1.45,
    },
    "GLASS": {
        "label": "Glass",
        "base_color": (1.0, 1.0, 1.0, 1.0),
        "metallic": 0.0,
        "roughness": 0.0,
        "ior": 1.45,
        "transmission": 1.0,
    },
    "PAINT": {
        "label": "Paint",
        "base_color": (0.75, 0.12, 0.1, 1.0),
        "metallic": 0.0,
        "roughness": 0.4,
        "ior": 1.45,
        "coat": 0.85,
    },
}


def _apply_preset(mat: bpy.types.Material, preset: dict) -> None:
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        return
    bsdf.inputs["Base Color"].default_value = preset["base_color"]
    bsdf.inputs["Metallic"].default_value = preset["metallic"]
    bsdf.inputs["Roughness"].default_value = preset["roughness"]
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = preset.get("ior", 1.45)
    transmission = preset.get("transmission", 0.0)
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    coat = preset.get("coat", 0.0)
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    elif "Clearcoat" in bsdf.inputs:
        bsdf.inputs["Clearcoat"].default_value = coat


def apply_to_objects(objects: list[bpy.types.Object], preset_id: str) -> int:
    preset = PRESETS[preset_id]
    mat_name = f"BEHOLD_{preset_id.title()}"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    _apply_preset(mat, preset)
    count = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        count += 1
    return count


class BEHOLD_OT_apply_local_material(Operator):
    bl_idname = "behold.apply_local_material"
    bl_label = "Apply Local Material"
    bl_description = "Assign a built-in PBR preset to selected meshes"
    bl_options = {"REGISTER", "UNDO"}

    preset: EnumProperty(
        name="Preset",
        items=tuple(
            (key, data["label"], f"Apply {data['label']} preset")
            for key, data in PRESETS.items()
        ),
        default="METAL",
    )

    def execute(self, context: Context):
        targets = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not targets:
            self.report({"ERROR"}, "Select at least one mesh object")
            return {"CANCELLED"}
        count = apply_to_objects(targets, self.preset)
        self.report({"INFO"}, f"Applied {PRESETS[self.preset]['label']} to {count} object(s)")
        return {"FINISHED"}


CLASSES = (BEHOLD_OT_apply_local_material,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin OCP / OpenCASCADE STEP to Blender mesh importer."""

from __future__ import annotations

import os
from typing import Any

import bpy
from mathutils import Vector


def _ensure_ocp() -> dict:
    """Import OCP symbols. Raises ImportError if missing."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location

    return {
        "BRep_Tool": BRep_Tool,
        "BRepMesh_IncrementalMesh": BRepMesh_IncrementalMesh,
        "IFSelect_RetDone": IFSelect_RetDone,
        "STEPControl_Reader": STEPControl_Reader,
        "TopAbs_FACE": TopAbs_FACE,
        "TopExp_Explorer": TopExp_Explorer,
        "TopLoc_Location": TopLoc_Location,
    }


def _get_triangulation(face, location, BRep_Tool):
    """Return a triangulation across OCP API variants."""
    for attr in ("Triangulation_s", "Triangulation"):
        fn = getattr(BRep_Tool, attr, None)
        if fn is None:
            continue
        try:
            return fn(face, location)
        except TypeError:
            try:
                return fn(face, location, True)
            except TypeError:
                continue
    return None


def _iter_nodes(triangulation, trsf) -> list[Vector]:
    verts: list[Vector] = []
    if hasattr(triangulation, "NbNodes") and hasattr(triangulation, "Node"):
        for i in range(1, triangulation.NbNodes() + 1):
            p = triangulation.Node(i)
            p.Transform(trsf)
            verts.append(Vector((p.X(), p.Y(), p.Z())))
        return verts
    nodes = triangulation.Nodes()
    for i in range(1, nodes.Length() + 1):
        p = nodes.Value(i)
        p.Transform(trsf)
        verts.append(Vector((p.X(), p.Y(), p.Z())))
    return verts


def _iter_triangles(triangulation) -> list[tuple[int, int, int]]:
    triangles: list[tuple[int, int, int]] = []
    if hasattr(triangulation, "NbTriangles") and hasattr(triangulation, "Triangle"):
        for i in range(1, triangulation.NbTriangles() + 1):
            tri = triangulation.Triangle(i)
            n1, n2, n3 = tri.Get()
            triangles.append((n1 - 1, n2 - 1, n3 - 1))
        return triangles
    tris = triangulation.Triangles()
    for i in range(1, tris.Length() + 1):
        tri = tris.Value(i)
        n1, n2, n3 = tri.Get()
        triangles.append((n1 - 1, n2 - 1, n3 - 1))
    return triangles


def _face_to_triangles(face, ocp: dict) -> tuple[list[Vector], list[tuple[int, int, int]]]:
    location = ocp["TopLoc_Location"]()
    triangulation = _get_triangulation(face, location, ocp["BRep_Tool"])
    if triangulation is None:
        return [], []
    trsf = location.Transformation()
    return _iter_nodes(triangulation, trsf), _iter_triangles(triangulation)


def import_step_with_ocp(
    filepath: str,
    *,
    deflection: float = 0.001,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """Read a STEP file via OCP, tessellate, and create mesh objects."""
    path = bpy.path.abspath(filepath)
    if not path or not os.path.isfile(path):
        return {"ok": False, "objects": [], "message": f"File not found: {filepath}"}

    try:
        ocp = _ensure_ocp()
    except ImportError as exc:
        return {"ok": False, "objects": [], "message": f"OCP not available ({exc})"}

    reader = ocp["STEPControl_Reader"]()
    status = reader.ReadFile(path)
    if status != ocp["IFSelect_RetDone"]:
        return {"ok": False, "objects": [], "message": "STEPControl_Reader failed to read file"}

    reader.TransferRoots()
    shape = reader.OneShape()
    if shape is None or shape.IsNull():
        return {"ok": False, "objects": [], "message": "No shape transferred from STEP"}

    ocp["BRepMesh_IncrementalMesh"](shape, deflection, False, 0.5, True)

    all_verts: list[Vector] = []
    all_faces: list[tuple[int, int, int]] = []
    explorer = ocp["TopExp_Explorer"](shape, ocp["TopAbs_FACE"])
    while explorer.More():
        face = explorer.Current()
        verts, tris = _face_to_triangles(face, ocp)
        base = len(all_verts)
        all_verts.extend(verts)
        all_faces.extend((base + a, base + b, base + c) for a, b, c in tris)
        explorer.Next()

    if not all_verts or not all_faces:
        return {
            "ok": False,
            "objects": [],
            "message": "Tessellation produced no triangles — try a finer deflection",
        }

    stem = os.path.splitext(os.path.basename(path))[0] or "BEHOLD_STEP"
    mesh = bpy.data.meshes.new(f"{stem}_Mesh")
    mesh.from_pydata([(v.x, v.y, v.z) for v in all_verts], [], all_faces)
    mesh.validate(clean_customdata=False)
    mesh.update()

    obj = bpy.data.objects.new(stem, mesh)
    obj["BEHOLD_cad_source"] = path
    obj["BEHOLD_cad_backend"] = "OCP"

    col_name = collection_name or f"BEHOLD_CAD_{stem}"
    collection = bpy.data.collections.get(col_name)
    if collection is None:
        collection = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return {
        "ok": True,
        "objects": [obj],
        "message": f"Imported “{stem}” via OCP ({len(all_faces)} tris)",
    }

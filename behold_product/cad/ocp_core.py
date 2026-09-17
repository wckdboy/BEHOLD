# SPDX-License-Identifier: GPL-3.0-or-later
"""OCP STEP / IGES / BREP read + tessellate (no Blender).

OCP is an optional site package. Imports stay in this module's try/except
so mesh-only CI and sessions without OpenCASCADE still load.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from OCP.BRep import BRep_Builder, BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS_Shape

    _OCP_IMPORT_ERROR: BaseException | None = None
except Exception as exc:  # noqa: BLE001
    BRep_Builder = None  # type: ignore[assignment]
    BRep_Tool = None  # type: ignore[assignment]
    BRepMesh_IncrementalMesh = None  # type: ignore[assignment]
    BRepTools = None  # type: ignore[assignment]
    IFSelect_RetDone = None  # type: ignore[assignment]
    STEPControl_Reader = None  # type: ignore[assignment]
    TopAbs_FACE = None  # type: ignore[assignment]
    TopExp_Explorer = None  # type: ignore[assignment]
    TopLoc_Location = None  # type: ignore[assignment]
    TopoDS_Shape = None  # type: ignore[assignment]
    _OCP_IMPORT_ERROR = exc

try:
    from OCP.IGESControl import IGESControl_Reader
except Exception:  # noqa: BLE001
    IGESControl_Reader = None  # type: ignore[assignment]


def probe_ocp() -> dict[str, Any]:
    """UI-oriented OCP status. Never raises."""
    if _OCP_IMPORT_ERROR is None:
        return {
            "available": True,
            "label": "OCP ready",
            "detail": "OpenCASCADE (OCP) bindings found — BEHOLD can import STEP itself.",
        }
    return {
        "available": False,
        "label": "OCP not installed",
        "detail": (
            "Install STEPper NEXT from "
            "https://github.com/Peak-Design/STEPper_NEXT/releases "
            "(Blender 5.1+/5.2 LTS) or add cadquery-ocp / cadquery-ocp-novtk "
            f"into Blender's Python. ({type(_OCP_IMPORT_ERROR).__name__})"
        ),
    }


def ocp_available() -> bool:
    return _OCP_IMPORT_ERROR is None


def ensure_ocp() -> dict[str, Any]:
    """Return OCP symbols. Raises ImportError if bindings are missing."""
    if _OCP_IMPORT_ERROR is not None:
        raise ImportError(
            f"OCP not available ({type(_OCP_IMPORT_ERROR).__name__}: {_OCP_IMPORT_ERROR})"
        ) from _OCP_IMPORT_ERROR
    return {
        "BRep_Tool": BRep_Tool,
        "BRepMesh_IncrementalMesh": BRepMesh_IncrementalMesh,
        "IFSelect_RetDone": IFSelect_RetDone,
        "STEPControl_Reader": STEPControl_Reader,
        "TopAbs_FACE": TopAbs_FACE,
        "TopExp_Explorer": TopExp_Explorer,
        "TopLoc_Location": TopLoc_Location,
    }


def read_cad_shape(path: str) -> tuple[Any, str | None]:
    """Load a CAD file into an OpenCASCADE shape. Returns (shape, error)."""
    try:
        ocp = ensure_ocp()
    except ImportError as exc:
        return None, str(exc)

    ext = os.path.splitext(path)[1].lower()

    if ext in {".iges", ".igs"}:
        if IGESControl_Reader is None:
            return None, "IGES reader unavailable"
        reader = IGESControl_Reader()
        status = reader.ReadFile(path)
        if status != ocp["IFSelect_RetDone"]:
            return None, "IGESControl_Reader failed to read file"
        reader.TransferRoots()
        shape = reader.OneShape()
        if shape is None or shape.IsNull():
            return None, "No shape transferred from IGES"
        return shape, None

    if ext in {".brep", ".brp"}:
        if BRep_Builder is None or BRepTools is None or TopoDS_Shape is None:
            return None, "BREP reader unavailable"
        shape = TopoDS_Shape()
        builder = BRep_Builder()
        read_fns = (
            getattr(BRepTools, "Read_s", None),
            getattr(BRepTools, "Read", None),
        )
        last_error = "BRepTools.Read is not available"
        for fn in read_fns:
            if fn is None:
                continue
            try:
                ok = fn(shape, path, builder)
            except TypeError:
                try:
                    ok = fn(path, shape, builder)
                except TypeError as exc:
                    last_error = str(exc)
                    continue
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                continue
            if ok is False:
                last_error = "BRepTools.Read returned false"
                continue
            if shape.IsNull():
                last_error = "BREP file produced an empty shape"
                continue
            return shape, None
        return None, last_error

    reader = ocp["STEPControl_Reader"]()
    status = reader.ReadFile(path)
    if status != ocp["IFSelect_RetDone"]:
        return None, "STEPControl_Reader failed to read file"
    reader.TransferRoots()
    shape = reader.OneShape()
    if shape is None or shape.IsNull():
        return None, "No shape transferred from STEP"
    return shape, None


def _get_triangulation(face: Any, location: Any, tool: Any) -> Any:
    """Return a triangulation across OCP API variants."""
    for attr in ("Triangulation_s", "Triangulation"):
        fn = getattr(tool, attr, None)
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


def _iter_nodes(triangulation: Any, trsf: Any) -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    if hasattr(triangulation, "NbNodes") and hasattr(triangulation, "Node"):
        for i in range(1, triangulation.NbNodes() + 1):
            point = triangulation.Node(i)
            point.Transform(trsf)
            verts.append((point.X(), point.Y(), point.Z()))
        return verts
    nodes = triangulation.Nodes()
    for i in range(1, nodes.Length() + 1):
        point = nodes.Value(i)
        point.Transform(trsf)
        verts.append((point.X(), point.Y(), point.Z()))
    return verts


def _iter_triangles(triangulation: Any) -> list[tuple[int, int, int]]:
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


def _face_to_triangles(
    face: Any, ocp: dict[str, Any]
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    location = ocp["TopLoc_Location"]()
    triangulation = _get_triangulation(face, location, ocp["BRep_Tool"])
    if triangulation is None:
        return [], []
    trsf = location.Transformation()
    return _iter_nodes(triangulation, trsf), _iter_triangles(triangulation)


def tessellate_shape(
    shape: Any,
    *,
    deflection: float = 0.001,
    angular_deflection: float = 0.5,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Mesh an OpenCASCADE shape. Returns (vertices, triangle indices)."""
    ocp = ensure_ocp()
    ocp["BRepMesh_IncrementalMesh"](shape, deflection, False, angular_deflection, True)

    all_verts: list[tuple[float, float, float]] = []
    all_faces: list[tuple[int, int, int]] = []
    explorer = ocp["TopExp_Explorer"](shape, ocp["TopAbs_FACE"])
    while explorer.More():
        face = explorer.Current()
        verts, tris = _face_to_triangles(face, ocp)
        base = len(all_verts)
        all_verts.extend(verts)
        all_faces.extend((base + a, base + b, base + c) for a, b, c in tris)
        explorer.Next()
    return all_verts, all_faces

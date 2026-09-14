#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Write a 10 mm axis-aligned cube as AP214 STEP (self-generated, CC0)."""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "unit_cube.step"

SIZE = 10.0
FILE_STAMP = "2026-09-13T00:00:00"


class _Writer:
    def __init__(self) -> None:
        self._next = 1
        self.lines: list[str] = []

    def add(self, body: str) -> int:
        ident = self._next
        self._next += 1
        self.lines.append(f"#{ident}={body};")
        return ident


def _ref_list(ids: list[int]) -> str:
    return "(" + ",".join(f"#{i}" for i in ids) + ")"


def build_step() -> str:
    w = _Writer()
    ctx = w.add("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    w.add(
        "APPLICATION_PROTOCOL_DEFINITION('international standard',"
        f"'automotive_design',2000,#{ctx})"
    )
    product_ctx = w.add(f"PRODUCT_CONTEXT('',#{ctx},'mechanical')")
    product = w.add(
        "PRODUCT('unit_cube','BEHOLD unit cube',"
        f"'10 mm axis-aligned box',(#{product_ctx}))"
    )
    pdf = w.add(f"PRODUCT_DEFINITION_FORMATION('','',#{product})")
    pdc = w.add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{ctx},'design')")
    pd = w.add(f"PRODUCT_DEFINITION('design','',#{pdf},#{pdc})")
    pds = w.add(f"PRODUCT_DEFINITION_SHAPE('','',#{pd})")

    length = w.add("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
    angle = w.add("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
    solid = w.add("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
    uncertainty = w.add(
        f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-6),#{length},"
        "'distance_accuracy_value','')"
    )
    geom_ctx = w.add(
        "(GEOMETRIC_REPRESENTATION_CONTEXT(3)"
        f"GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{uncertainty}))"
        f"GLOBAL_UNIT_ASSIGNED_CONTEXT((#{length},#{angle},#{solid}))"
        "REPRESENTATION_CONTEXT('Context','3D'))"
    )

    corners = (
        (0.0, 0.0, 0.0),
        (SIZE, 0.0, 0.0),
        (SIZE, SIZE, 0.0),
        (0.0, SIZE, 0.0),
        (0.0, 0.0, SIZE),
        (SIZE, 0.0, SIZE),
        (SIZE, SIZE, SIZE),
        (0.0, SIZE, SIZE),
    )
    points = [
        w.add(f"CARTESIAN_POINT('',({x:.1f},{y:.1f},{z:.1f}))") for x, y, z in corners
    ]
    vertices = [w.add(f"VERTEX_POINT('',#{pid})") for pid in points]

    directions: dict[tuple[int, int, int], int] = {}

    def direction(vec: tuple[float, float, float]) -> int:
        key = (int(vec[0]), int(vec[1]), int(vec[2]))
        if key not in directions:
            directions[key] = w.add(
                f"DIRECTION('',({float(vec[0]):.1f},{float(vec[1]):.1f},{float(vec[2]):.1f}))"
            )
        return directions[key]

    # Canonical undirected edges (lower vertex index first).
    undirected = (
        (0, 1),
        (1, 2),
        (2, 3),
        (0, 3),
        (4, 5),
        (5, 6),
        (6, 7),
        (4, 7),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    edge_curves: dict[tuple[int, int], int] = {}
    for a, b in undirected:
        ax, ay, az = corners[a]
        bx, by, bz = corners[b]
        dx, dy, dz = bx - ax, by - ay, bz - az
        length_mm = max(abs(dx), abs(dy), abs(dz))
        unit = (
            1.0 if dx > 0 else (-1.0 if dx < 0 else 0.0),
            1.0 if dy > 0 else (-1.0 if dy < 0 else 0.0),
            1.0 if dz > 0 else (-1.0 if dz < 0 else 0.0),
        )
        vec = w.add(f"VECTOR('',#{direction(unit)},{length_mm:.1f})")
        line = w.add(f"LINE('',#{points[a]},#{vec})")
        edge_curves[(a, b)] = w.add(
            f"EDGE_CURVE('',#{vertices[a]},#{vertices[b]},#{line},.T.)"
        )

    # Vertex cycles, CCW when viewed from outside (outward normal).
    faces = (
        ((0, 3, 2, 1), (0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        ((4, 5, 6, 7), (0.0, 0.0, 1.0), (0.0, 0.0, SIZE), (1.0, 0.0, 0.0)),
        ((0, 1, 5, 4), (0.0, -1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        ((2, 3, 7, 6), (0.0, 1.0, 0.0), (0.0, SIZE, 0.0), (-1.0, 0.0, 0.0)),
        ((0, 4, 7, 3), (-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        ((1, 2, 6, 5), (1.0, 0.0, 0.0), (SIZE, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )

    advanced_faces: list[int] = []
    for cycle, normal, origin, ref_dir in faces:
        oriented: list[int] = []
        for i, start in enumerate(cycle):
            end = cycle[(i + 1) % len(cycle)]
            a, b = (start, end) if start < end else (end, start)
            same = start < end
            flag = ".T." if same else ".F."
            oriented.append(
                w.add(f"ORIENTED_EDGE('',*,*,#{edge_curves[(a, b)]},{flag})")
            )
        loop = w.add(f"EDGE_LOOP('',{_ref_list(oriented)})")
        bound = w.add(f"FACE_OUTER_BOUND('',#{loop},.T.)")
        ox, oy, oz = origin
        origin_pt = w.add(f"CARTESIAN_POINT('',({ox:.1f},{oy:.1f},{oz:.1f}))")
        placement = w.add(
            "AXIS2_PLACEMENT_3D('',"
            f"#{origin_pt},#{direction(normal)},#{direction(ref_dir)})"
        )
        plane = w.add(f"PLANE('',#{placement})")
        advanced_faces.append(
            w.add(f"ADVANCED_FACE('',(#{bound}),#{plane},.T.)")
        )

    shell = w.add(f"CLOSED_SHELL('',{_ref_list(advanced_faces)})")
    solid_brep = w.add(f"MANIFOLD_SOLID_BREP('unit_cube',#{shell})")
    shape_rep = w.add(
        f"ADVANCED_BREP_SHAPE_REPRESENTATION('',(#{solid_brep}),#{geom_ctx})"
    )
    w.add(f"SHAPE_DEFINITION_REPRESENTATION(#{pds},#{shape_rep})")

    header = (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('BEHOLD self-generated 10 mm unit cube'),'2;1');\n"
        f"FILE_NAME('unit_cube.step','{FILE_STAMP}',('BEHOLD contributors'),"
        "('BEHOLD'),'generate_unit_cube.py','BEHOLD','CC0-1.0');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\n"
        "ENDSEC;\n"
        "DATA;\n"
    )
    return header + "\n".join(w.lines) + "\nENDSEC;\nEND-ISO-10303-21;\n"


def main() -> None:
    OUT.write_text(build_step(), encoding="ascii")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

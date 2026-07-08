"""Recursive BSP-tree partition walls (see doc section 4 pseudocode).

Each call to build_partitions() walks the validated partition tree and
produces:
  - a single unioned CadQuery solid containing every divider wall
  - a flat list of "wall specs" describing each wall's own rectangular
    hollow-able face, consumed later by hollow.py to punch pill-hole
    vents into individual dividers without re-deriving their geometry.

Coordinates follow body.py's convention (origin centered on X/Y, Z=0 at the
bed). The inner cavity footprint is the box's XY extent inset by `wall` on
every side; its floor sits at Z=wall (on top of the bottom slab).
"""
from __future__ import annotations

from typing import Optional

import cadquery as cq


def _make_wall_solid(x0, x1, y0, y1, z0, z1, top_fillet=0.0) -> cq.Workplane:
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    wall = (
        cq.Workplane("XY")
        .box(dx, dy, dz, centered=(True, True, False))
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, z0))
    )
    # Round the wall's top rim so the exposed divider edge isn't a sharp,
    # hand-cutting corner (mirrors the box's own top-rim fillet). Bounded by
    # half the wall thickness; guarded because very thin/short walls can make
    # OCCT refuse the fillet.
    if top_fillet > 0:
        try:
            wall = wall.faces(">Z").edges().fillet(top_fillet)
        except Exception:
            pass
    return wall


def _wall_top_fillet(thickness: float) -> float:
    """Safe top-rim fillet radius for a divider of the given thickness."""
    return thickness * 0.45


def _build_recursive(node: Optional[dict], region: dict, floor_z: float, ceiling_z: float, out_walls, out_specs):
    if node is None:
        return
    split = node["split"]
    axis = split["axis"]
    at = split["at"]
    thickness = split["thickness"]
    height = split["height"]

    z0 = floor_z
    z1 = ceiling_z if height is None else min(floor_z + height, ceiling_z)

    top_fillet = _wall_top_fillet(thickness)

    if axis == "x":
        center = region["x0"] + at
        a, b = center - thickness / 2, center + thickness / 2
        wall = _make_wall_solid(a, b, region["y0"], region["y1"], z0, z1, top_fillet)
        out_walls.append(wall)
        out_specs.append(
            {
                "axis": "x",
                "center": center,
                "thickness": thickness,
                "span0": region["y0"],
                "span1": region["y1"],
                "z0": z0,
                "z1": z1,
            }
        )
        sub_a = {"x0": region["x0"], "x1": a, "y0": region["y0"], "y1": region["y1"]}
        sub_b = {"x0": b, "x1": region["x1"], "y0": region["y0"], "y1": region["y1"]}
    else:
        center = region["y0"] + at
        a, b = center - thickness / 2, center + thickness / 2
        wall = _make_wall_solid(region["x0"], region["x1"], a, b, z0, z1, top_fillet)
        out_walls.append(wall)
        out_specs.append(
            {
                "axis": "y",
                "center": center,
                "thickness": thickness,
                "span0": region["x0"],
                "span1": region["x1"],
                "z0": z0,
                "z1": z1,
            }
        )
        sub_a = {"x0": region["x0"], "x1": region["x1"], "y0": region["y0"], "y1": a}
        sub_b = {"x0": region["x0"], "x1": region["x1"], "y0": b, "y1": region["y1"]}

    _build_recursive(node["children"][0], sub_a, floor_z, ceiling_z, out_walls, out_specs)
    _build_recursive(node["children"][1], sub_b, floor_z, ceiling_z, out_walls, out_specs)


def build_partitions(tree: Optional[dict], box_cfg: dict):
    """Returns (solid_or_None, wall_specs)."""
    if tree is None:
        return None, []

    wall = box_cfg["wall"]
    length, width, height = box_cfg["length"], box_cfg["width"], box_cfg["height"]
    region = {
        "x0": -(length / 2 - wall),
        "x1": (length / 2 - wall),
        "y0": -(width / 2 - wall),
        "y1": (width / 2 - wall),
    }
    floor_z = wall
    ceiling_z = height

    walls, specs = [], []
    _build_recursive(tree, region, floor_z, ceiling_z, walls, specs)

    solid = walls[0]
    for w in walls[1:]:
        solid = solid.union(w)
    return solid, specs

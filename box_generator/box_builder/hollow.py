"""45-degree pill-hole vent arrays (see doc section 5.3).

Fixed at 45 degrees for support-free bridging; only hole_size is exposed,
spacing/border are derived. Never applied to outer walls -- only to the
bottom slab and/or partition dividers, both of which we already know the
exact analytic rectangle for (no fragile face auto-discovery needed).
"""
from __future__ import annotations

import math
from typing import Optional

import cadquery as cq

PILL_LENGTH_RATIO = 2.5  # pill length = hole_size * ratio
MIN_GAP = 0.8  # minimum bridge wall left between adjacent holes
EPS = 0.5  # extra cut margin so booleans always fully perforate


def _rotated_bbox_half_extents(length: float, diameter: float, angle_deg: float):
    theta = math.radians(angle_deg)
    half_l, half_d = length / 2, diameter / 2
    half_x = half_l * abs(math.cos(theta)) + half_d * abs(math.sin(theta))
    half_y = half_l * abs(math.sin(theta)) + half_d * abs(math.cos(theta))
    return half_x, half_y


def _generate_pill_centers(min_u, max_u, min_v, max_v, spacing, angle_deg, half_x, half_y):
    """Build a grid of pill centers, rotated as a whole array by angle_deg,
    keeping only pills that fit entirely inside [min_u,max_u]x[min_v,max_v]."""
    if max_u - min_u <= 2 * half_x or max_v - min_v <= 2 * half_y:
        return []
    cu, cv = (min_u + max_u) / 2, (min_v + max_v) / 2
    diag = math.hypot(max_u - min_u, max_v - min_v)
    n = int(diag / (2 * spacing)) + 2
    theta = math.radians(angle_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    centers = []
    for i in range(-n, n + 1):
        p = i * spacing
        for j in range(-n, n + 1):
            q = j * spacing
            u = cu + p * cos_t - q * sin_t
            v = cv + p * sin_t + q * cos_t
            if (min_u + half_x <= u <= max_u - half_x) and (min_v + half_y <= v <= max_v - half_y):
                centers.append((u, v))
    return centers


def _pill_grid_params(hole_size: float, angle: float):
    pill_length = hole_size * PILL_LENGTH_RATIO
    gap = max(hole_size * 0.4, MIN_GAP)
    spacing = hole_size + gap
    half_x, half_y = _rotated_bbox_half_extents(pill_length, hole_size, angle)
    return pill_length, spacing, half_x, half_y


def _build_cutter(plane_name: str, offset: float, min_u, max_u, min_v, max_v, thickness, hollow_cfg) -> Optional[cq.Workplane]:
    hole_size = hollow_cfg["hole_size"]
    angle = hollow_cfg["angle"]
    border = hollow_cfg["border"]

    pill_length, spacing, half_x, half_y = _pill_grid_params(hole_size, angle)
    centers = _generate_pill_centers(
        min_u + border, max_u - border, min_v + border, max_v - border, spacing, angle, half_x, half_y
    )
    if not centers:
        return None

    extrude_dist = thickness / 2 + EPS
    cutter = (
        cq.Workplane(plane_name)
        .workplane(offset=offset)
        .pushPoints(centers)
        .slot2D(pill_length, hole_size, angle)
        .extrude(extrude_dist, both=True)
    )
    return cutter


def apply_bottom_hollow(solid: cq.Workplane, box_cfg: dict, hollow_cfg: dict) -> cq.Workplane:
    wall = box_cfg["wall"]
    length, width = box_cfg["length"], box_cfg["width"]
    x0, x1 = -(length / 2 - wall), (length / 2 - wall)
    y0, y1 = -(width / 2 - wall), (width / 2 - wall)

    cutter = _build_cutter("XY", wall / 2, x0, x1, y0, y1, wall, hollow_cfg)
    if cutter is None:
        return solid
    return solid.cut(cutter)


def apply_partition_hollow(solid: cq.Workplane, wall_specs: list, hollow_cfg: dict) -> cq.Workplane:
    for spec in wall_specs:
        if spec["axis"] == "x":
            # plane "YZ": local x = world Y, local y = world Z, normal = world X
            cutter = _build_cutter(
                "YZ", spec["center"], spec["span0"], spec["span1"], spec["z0"], spec["z1"],
                spec["thickness"], hollow_cfg,
            )
        else:
            # plane "ZX": local x = world Z, local y = world X, normal = world Y
            cutter = _build_cutter(
                "ZX", spec["center"], spec["z0"], spec["z1"], spec["span0"], spec["span1"],
                spec["thickness"], hollow_cfg,
            )
        if cutter is not None:
            solid = solid.cut(cutter)
    return solid


def apply_hollow(solid: cq.Workplane, box_cfg: dict, wall_specs: list, hollow_cfg: dict) -> cq.Workplane:
    if hollow_cfg["faces"]["bottom"]:
        solid = apply_bottom_hollow(solid, box_cfg, hollow_cfg)
    if hollow_cfg["faces"]["partitions"] and wall_specs:
        solid = apply_partition_hollow(solid, wall_specs, hollow_cfg)
    return solid

"""Load and validate the box-generator YAML config.

Turns the raw YAML dict into a validated, clamped, plain-dict config that the
rest of box_builder can consume without re-checking bounds.
"""
from __future__ import annotations

import sys
from typing import Any, Optional

import yaml

MAX_PLATE_XY = 250.0  # printer bed is 256x256, 6mm safety margin
DEFAULT_Z_MAX = 250.0
MIN_GAP = 0.8  # minimum bridge wall left between adjacent hollow holes


class ConfigError(ValueError):
    """Raised for hard validation failures (must abort, never silently fix)."""


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return validate_config(raw)


def _warn(msg: str) -> None:
    print(f"[warn] {msg}", file=sys.stderr)


def _validate_box(raw_box: dict) -> dict:
    size = raw_box.get("size")
    if not size or len(size) != 3:
        raise ConfigError("box.size must be a [length, width, height] triple")
    length, width, height = (float(v) for v in size)

    if length <= 0 or width <= 0 or height <= 0:
        raise ConfigError("box.size values must all be positive")
    if length > MAX_PLATE_XY or width > MAX_PLATE_XY:
        raise ConfigError(
            f"box length/width must be <= {MAX_PLATE_XY}mm to fit the 256x256 "
            f"print bed with safety margin (got {length} x {width})"
        )
    z_max = float(raw_box.get("z_max", DEFAULT_Z_MAX))
    if height > z_max:
        raise ConfigError(f"box height {height} exceeds z_max {z_max}")

    wall = float(raw_box.get("wall", 2))
    if wall <= 0:
        raise ConfigError("box.wall must be positive")
    if wall * 2 >= min(length, width):
        raise ConfigError("box.wall is too thick for the given length/width")

    corner_radius = float(raw_box.get("corner_radius", 0))
    max_corner = min(length, width) / 2 * 0.9
    if corner_radius < 0:
        raise ConfigError("box.corner_radius must be >= 0")
    if corner_radius > max_corner:
        _warn(
            f"corner_radius {corner_radius} exceeds geometric limit "
            f"{max_corner:.3f}, clamping"
        )
        corner_radius = max(max_corner, 0.0)

    ef_raw = raw_box.get("edge_fillet", {}) or {}
    top = float(ef_raw.get("top", 0))
    bottom = float(ef_raw.get("bottom", 0))
    if top < 0 or bottom < 0:
        raise ConfigError("edge_fillet values must be >= 0")

    # Top rim fillet rounds both the outer AND inner rim edge at once. Those
    # two fillets eat into the flat rim from opposite sides, so they meet
    # (and OCCT fails to build them) once the radius reaches wall/2 -- not
    # wall. Leave a safety margin below that true geometric limit.
    max_top = wall / 2 * 0.9
    if top > max_top:
        _warn(f"edge_fillet.top {top} exceeds safe limit, clamping to {max_top:.3f}")
        top = max(max_top, 0.0)

    max_bottom = min(height, min(length, width) / 2) * 0.8
    if bottom > max_bottom:
        _warn(f"edge_fillet.bottom {bottom} exceeds safe limit, clamping to {max_bottom:.3f}")
        bottom = max(max_bottom, 0.0)

    return {
        "length": length,
        "width": width,
        "height": height,
        "wall": wall,
        "corner_radius": corner_radius,
        "edge_fillet": {"top": top, "bottom": bottom},
    }


def _resolve_split_at(at: Any, span: float) -> float:
    """Resolve a split position (fraction or 'Nmm' string) to an absolute mm offset."""
    if isinstance(at, str):
        s = at.strip().lower()
        if not s.endswith("mm"):
            raise ConfigError(f"partition 'at' string must end in 'mm', got {at!r}")
        return float(s[:-2])
    at = float(at)
    if 0 <= at <= 1:
        return at * span
    return at


def _validate_partition_node(
    node: Optional[dict], span_x: float, span_y: float, wall: float, box_height: float
) -> Optional[dict]:
    if node is None:
        return None
    split = node.get("split")
    if not split:
        raise ConfigError("partition node must have a 'split' key (or be null)")

    axis = split.get("axis")
    if axis not in ("x", "y"):
        raise ConfigError(f"partition split.axis must be 'x' or 'y', got {axis!r}")
    span = span_x if axis == "x" else span_y

    thickness = float(split.get("thickness", wall))
    if thickness <= 0:
        raise ConfigError("partition split.thickness must be positive")

    at = _resolve_split_at(split.get("at", 0.5), span)
    if at - thickness / 2 <= 0 or at + thickness / 2 >= span:
        raise ConfigError(
            f"partition split at={at} thickness={thickness} does not fit "
            f"within span {span} on axis {axis}"
        )

    height = split.get("height", None)
    if height is not None:
        height = float(height)
        if height <= 0 or height > box_height:
            raise ConfigError(f"partition split.height {height} out of range (0, {box_height}]")

    children_raw = node.get("children", [None, None])
    if len(children_raw) != 2:
        raise ConfigError("partition node.children must have exactly 2 entries")

    if axis == "x":
        span_a = at - thickness / 2
        span_b = span_x - at - thickness / 2
        child_a = _validate_partition_node(children_raw[0], span_a, span_y, wall, box_height)
        child_b = _validate_partition_node(children_raw[1], span_b, span_y, wall, box_height)
    else:
        span_a = at - thickness / 2
        span_b = span_y - at - thickness / 2
        child_a = _validate_partition_node(children_raw[0], span_x, span_a, wall, box_height)
        child_b = _validate_partition_node(children_raw[1], span_x, span_b, wall, box_height)

    return {
        "split": {"axis": axis, "at": at, "thickness": thickness, "height": height},
        "children": [child_a, child_b],
    }


def _validate_partitions(raw_partitions, box: dict) -> Optional[dict]:
    if raw_partitions is None:
        return None
    inner_x = box["length"] - 2 * box["wall"]
    inner_y = box["width"] - 2 * box["wall"]
    return _validate_partition_node(raw_partitions, inner_x, inner_y, box["wall"], box["height"])


def _validate_hollow(raw_hollow: dict, box: dict) -> dict:
    raw_hollow = raw_hollow or {}
    hole_size = float(raw_hollow.get("hole_size", 8))
    if hole_size <= 0:
        raise ConfigError("hollow.hole_size must be positive")

    angle = float(raw_hollow.get("angle", 45))
    if angle != 45:
        _warn("hollow.angle forced to 45 (fixed for support-free printing)")
        angle = 45.0

    border = raw_hollow.get("border", "auto")
    if border == "auto":
        border = max(box["wall"], hole_size * 0.5)
    else:
        border = float(border)
        if border < 0:
            raise ConfigError("hollow.border must be >= 0")

    faces_raw = raw_hollow.get("faces", {}) or {}
    faces = {
        "bottom": bool(faces_raw.get("bottom", False)),
        "partitions": bool(faces_raw.get("partitions", False)),
    }

    return {"hole_size": hole_size, "angle": angle, "border": border, "faces": faces}


def _validate_export(raw_export: dict) -> dict:
    raw_export = raw_export or {}
    fmt = raw_export.get("format", "stl")
    if fmt != "stl":
        raise ConfigError(f"only 'stl' export format is supported, got {fmt!r}")
    tolerance = float(raw_export.get("tolerance", 0.1))
    if tolerance <= 0:
        raise ConfigError("export.tolerance must be positive")
    filename = raw_export.get("filename", "box_output.stl")
    return {"format": fmt, "tolerance": tolerance, "filename": filename}


def validate_config(raw: dict) -> dict:
    if not raw or "box" not in raw:
        raise ConfigError("config must have a top-level 'box' section")

    box = _validate_box(raw["box"])
    partitions = _validate_partitions(raw.get("partitions"), box)
    hollow = _validate_hollow(raw.get("hollow"), box)
    export = _validate_export(raw.get("export"))

    return {"box": box, "partitions": partitions, "hollow": hollow, "export": export}

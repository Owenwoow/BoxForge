"""Config validation: hard limits, clamping, and public-deploy abuse guards.

Pure-Python (PyYAML only) -- no CadQuery, so these run in milliseconds.
"""
from __future__ import annotations

import pytest

from box_builder.validate import (
    MAX_PARTITION_DEPTH,
    MAX_PARTITION_NODES,
    MAX_PLATE_XY,
    ConfigError,
    _sanitize_filename,
    validate_config,
)


def _cfg(**box_overrides) -> dict:
    box = {"size": [120, 80, 40], "wall": 2, "corner_radius": 8, "edge_fillet": {"top": 1, "bottom": 1}}
    box.update(box_overrides)
    return {"box": box}


def _split(axis="x", at=0.5, children=(None, None)) -> dict:
    return {"split": {"axis": axis, "at": at, "thickness": 1.5}, "children": list(children)}


def test_minimal_config_gets_defaults():
    cfg = validate_config(_cfg())
    assert cfg["box"]["length"] == 120.0
    assert cfg["partitions"] is None
    assert cfg["hollow"]["faces"] == {"bottom": False, "partitions": False}
    assert cfg["export"] == {"format": "stl", "tolerance": 0.1, "filename": "box_output.stl"}


def test_missing_box_section_rejected():
    with pytest.raises(ConfigError):
        validate_config({})


@pytest.mark.parametrize("size", [[MAX_PLATE_XY + 1, 80, 40], [80, MAX_PLATE_XY + 1, 40]])
def test_oversize_footprint_rejected(size):
    with pytest.raises(ConfigError, match="print"):
        validate_config(_cfg(size=size))


@pytest.mark.parametrize("size", [[0, 80, 40], [120, -1, 40], [120, 80]])
def test_bad_size_rejected(size):
    with pytest.raises(ConfigError):
        validate_config(_cfg(size=size))


def test_wall_too_thick_rejected():
    with pytest.raises(ConfigError, match="wall"):
        validate_config(_cfg(size=[20, 20, 20], wall=10))


def test_corner_radius_clamped_to_geometric_limit():
    cfg = validate_config(_cfg(corner_radius=999))
    assert cfg["box"]["corner_radius"] == pytest.approx(80 / 2 * 0.9)


def test_top_fillet_clamped_below_half_wall():
    cfg = validate_config(_cfg(edge_fillet={"top": 5, "bottom": 0}))
    assert cfg["box"]["edge_fillet"]["top"] < 2 / 2


def test_split_at_accepts_fraction_and_mm():
    cfg = validate_config({**_cfg(), "partitions": _split(at="30mm")})
    assert cfg["partitions"]["split"]["at"] == 30.0
    cfg = validate_config({**_cfg(), "partitions": _split(at=0.25)})
    assert cfg["partitions"]["split"]["at"] == pytest.approx((120 - 4) * 0.25)


def test_split_outside_span_rejected():
    with pytest.raises(ConfigError, match="does not fit"):
        validate_config({**_cfg(), "partitions": _split(at="500mm")})


def test_bad_axis_rejected():
    with pytest.raises(ConfigError, match="axis"):
        validate_config({**_cfg(), "partitions": _split(axis="z")})


def test_partition_depth_capped():
    # A chain of tiny mm offsets keeps every split geometrically valid, so the
    # only thing that can stop it is the depth guard.
    node = None
    for _ in range(MAX_PARTITION_DEPTH + 2):
        node = _split(axis="x", at="2mm", children=(None, node))
    with pytest.raises(ConfigError, match="too deep"):
        validate_config({**_cfg(size=[250, 80, 40]), "partitions": node})


def test_partition_node_count_capped():
    # Balanced tree of depth MAX_PARTITION_DEPTH = 2^8 - 1 = 255 nodes > 200.
    def tree(depth: int):
        if depth == 0:
            return None
        axis = "x" if depth % 2 else "y"
        return _split(axis=axis, at=0.5, children=(tree(depth - 1), tree(depth - 1)))

    assert 2**MAX_PARTITION_DEPTH - 1 > MAX_PARTITION_NODES
    with pytest.raises(ConfigError, match="too many"):
        validate_config({**_cfg(size=[250, 250, 40]), "partitions": tree(MAX_PARTITION_DEPTH)})


def test_hollow_angle_forced_to_45():
    cfg = validate_config({**_cfg(), "hollow": {"angle": 30}})
    assert cfg["hollow"]["angle"] == 45.0


def test_only_stl_export_supported():
    with pytest.raises(ConfigError, match="stl"):
        validate_config({**_cfg(), "export": {"format": "step"}})


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("box.stl", "box.stl"),
        ("my box", "my box.stl"),
        ("../../etc/passwd", "passwd.stl"),
        ("C:\\Windows\\evil.stl", "evil.stl"),
        ("/abs/path/x.STL", "x.STL"),
        ("a$b|c.stl", "a_b_c.stl"),
        ("..", "box_output.stl"),
        ("", "box_output.stl"),
        (None, "box_output.stl"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert _sanitize_filename(raw) == expected

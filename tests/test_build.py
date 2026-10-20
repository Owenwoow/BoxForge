"""End-to-end modeling: real CadQuery / OpenCASCADE geometry and STL export."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from box_builder.validate import load_config, validate_config
from main import build_from_config

pytestmark = pytest.mark.slow

APP_DIR = Path(__file__).resolve().parents[1] / "box_generator"
SAMPLE_CONFIG = APP_DIR / "config.yaml"


def _solid_ok(solid) -> float:
    obj = solid.val()
    assert obj.isValid()
    volume = obj.Volume()
    assert volume > 0
    return volume


@pytest.fixture(scope="module")
def sample_raw() -> dict:
    return yaml.safe_load(SAMPLE_CONFIG.read_text(encoding="utf-8"))


def test_sample_config_builds_valid_solid():
    _solid_ok(build_from_config(load_config(str(SAMPLE_CONFIG))))


def test_plain_box_fits_declared_footprint(sample_raw):
    raw = copy.deepcopy(sample_raw)
    raw["partitions"] = None
    raw["hollow"]["faces"] = {"bottom": False, "partitions": False}
    solid = build_from_config(validate_config(raw))
    _solid_ok(solid)
    bb = solid.val().BoundingBox()
    assert bb.xlen == pytest.approx(120, abs=1e-3)
    assert bb.ylen == pytest.approx(80, abs=1e-3)
    assert bb.zlen == pytest.approx(40, abs=1e-3)


def test_partitions_and_hollow_change_volume(sample_raw):
    plain = copy.deepcopy(sample_raw)
    plain["hollow"]["faces"] = {"bottom": False, "partitions": False}
    solid_vol = _solid_ok(build_from_config(validate_config(plain)))
    hollow_vol = _solid_ok(build_from_config(validate_config(sample_raw)))
    # Pill vents remove material from the floor and dividers.
    assert hollow_vol < solid_vol


def test_cli_exports_stl(tmp_path):
    cfg = yaml.safe_load(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    cfg["export"]["filename"] = "ci_box.stl"
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(APP_DIR / "main.py"), str(cfg_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr
    out = tmp_path / "ci_box.stl"
    assert out.is_file() and out.stat().st_size > 1000


def test_cli_rejects_invalid_config(tmp_path):
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text("box: {size: [999, 80, 40]}\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(APP_DIR / "main.py"), str(cfg_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 1
    assert "[error]" in proc.stderr

"""STL export."""
from __future__ import annotations

import cadquery as cq


def export_stl(solid: cq.Workplane, export_cfg: dict) -> str:
    filename = export_cfg["filename"]
    cq.exporters.export(
        solid,
        filename,
        tolerance=export_cfg["tolerance"],
        angularTolerance=0.2,
    )
    return filename

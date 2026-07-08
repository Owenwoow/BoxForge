"""Box body: solid box -> vertical/bottom fillets -> shell -> top rim fillet.

Box coordinate convention used across this whole package:
  - Origin is centered on X/Y, sitting on the print bed at Z=0.
  - X spans [-length/2, length/2], Y spans [-width/2, width/2].
  - Z spans [0, height]; the box has an open top (no lid).
"""
from __future__ import annotations

import cadquery as cq
from cadquery import selectors


def build_body(box_cfg: dict) -> cq.Workplane:
    length = box_cfg["length"]
    width = box_cfg["width"]
    height = box_cfg["height"]
    wall = box_cfg["wall"]
    corner_radius = box_cfg["corner_radius"]
    edge_top = box_cfg["edge_fillet"]["top"]
    edge_bottom = box_cfg["edge_fillet"]["bottom"]

    solid = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

    # Vertical corner fillets: the 4 edges parallel to Z are exactly the 4
    # corner posts of a plain box, selected by direction (never by index).
    if corner_radius > 0:
        solid = solid.edges("|Z").fillet(corner_radius)

    # Bottom rim fillet: edges of the bottom face, restricted to straight
    # (LINE) edges so we don't try to re-fillet the corner-radius arcs.
    if edge_bottom > 0:
        solid = solid.faces("<Z").edges(selectors.TypeSelector("LINE")).fillet(edge_bottom)

    # Open the top: remove the top face, shell inward so outer dimensions
    # stay exactly [length, width, height].
    solid = solid.faces(">Z").shell(-wall)

    # Top rim fillet must happen after shelling: only now do the outer and
    # inner top edges both exist (the rim is the flat rectangular-ring face
    # left behind by the removed top face). Selecting its straight edges
    # rounds both the outer and inner lip in one fillet call.
    if edge_top > 0:
        solid = solid.faces(">Z").edges(selectors.TypeSelector("LINE")).fillet(edge_top)

    return solid

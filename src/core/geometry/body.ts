/**
 * Box body: solid box -> vertical/bottom fillets -> shell -> top rim fillet.
 *
 * Coordinate convention used across the whole geometry package:
 *   - Origin centered on X/Y, sitting on the print bed at Z=0.
 *   - X spans [-length/2, length/2], Y spans [-width/2, width/2].
 *   - Z spans [0, height]; the box has an open top (no lid).
 *
 * Order matters: the vertical corner fillets happen before shelling, and the
 * top rim fillet must come AFTER shelling (only then does the inner rim edge
 * exist). Edges are always picked by position, never by index.
 */
import { cast, drawRectangle, drawRoundedRectangle, FaceFinder, type Face, type Shape3D } from "replicad";
import type { BoxConfig } from "../config";
import { oc } from "./oc";

/**
 * Hollow `shape` inward by `thickness`, removing `faces` (the open side).
 *
 * replicad's own `shell()` calls MakeThickSolidByJoin with Intersection=false,
 * which fails as soon as an existing fillet is smaller than the wall (e.g. a
 * 1 mm bottom rim on a 2 mm wall). CadQuery passes Intersection=true, which
 * handles that case -- so we call OCCT directly with the same flags.
 */
export function shellInward(shape: Shape3D, thickness: number, faces: Face[]): Shape3D {
  const OC = oc();
  const toRemove = new OC.NCollection_List_TopoDS_Shape();
  const builder = new OC.BRepOffsetAPI_MakeThickSolid();
  try {
    for (const f of faces) toRemove.Append(f.wrapped);
    builder.MakeThickSolidByJoin(
      shape.wrapped,
      toRemove,
      -thickness,
      1e-3,
      OC.BRepOffset_Mode.BRepOffset_Skin,
      true, // Intersection
      false, // SelfInter
      OC.GeomAbs_JoinType.GeomAbs_Arc,
      false, // RemoveIntEdges
    );
    return cast(builder.Shape()) as Shape3D;
  } finally {
    builder.delete();
    toRemove.delete();
  }
}

export function buildBody(box: BoxConfig): Shape3D {
  const { length, width, height, wall, corner_radius: corner } = box;
  const { top, bottom } = box.edge_fillet;

  // Vertical corner fillets come for free from a rounded footprint.
  const footprint = corner > 0 ? drawRoundedRectangle(length, width, corner) : drawRectangle(length, width);
  let solid = footprint.sketchOnPlane("XY").extrude(height) as Shape3D;

  if (bottom > 0) solid = solid.fillet(bottom, (e) => e.inPlane("XY", 0));

  // Open the top: remove the top face, shell inward so the outer
  // dimensions stay exactly [length, width, height].
  solid = shellInward(solid, wall, new FaceFinder().inPlane("XY", height).find(solid) as Face[]);

  // The rim left behind is a flat ring at Z=height: filleting its edges
  // rounds the outer and the inner lip in one go.
  if (top > 0) solid = solid.fillet(top, (e) => e.inPlane("XY", height));

  return solid;
}

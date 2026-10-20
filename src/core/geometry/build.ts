/** Full model pipeline (same order as the Python main.build_from_config). */
import { measureShapeVolumeProperties, type Shape3D } from "replicad";
import type { Config } from "../config";
import { buildBody } from "./body";
import { applyHollow } from "./hollow";
import { oc } from "./oc";
import { buildPartitions } from "./partitions";

export function buildModel(cfg: Config): Shape3D {
  let solid = buildBody(cfg.box);
  const { walls, specs } = buildPartitions(cfg.partitions, cfg.box);
  for (const w of walls) solid = solid.fuse(w);
  return applyHollow(solid, cfg.box, specs, cfg.hollow);
}

export interface ModelStats {
  size: [number, number, number];
  /** mm^3 */
  volume: number;
  valid: boolean;
}

export function modelStats(shape: Shape3D): ModelStats {
  const [[x0, y0, z0], [x1, y1, z1]] = shape.boundingBox.bounds;
  const props = measureShapeVolumeProperties(shape);
  const volume = props.volume;
  props.delete();
  const OC = oc();
  const checker = new OC.BRepCheck_Analyzer(shape.wrapped, true, false);
  const valid = checker.IsValid();
  checker.delete();
  return { size: [x1 - x0, y1 - y0, z1 - z0], volume, valid };
}

export interface PreviewMesh {
  vertices: Float32Array;
  normals: Float32Array;
  triangles: Uint32Array;
}

/** Fine tessellation for a smooth preview (coarse tolerance looks faceted). */
export function previewMesh(shape: Shape3D): PreviewMesh {
  const m = shape.mesh({ tolerance: 0.05, angularTolerance: 0.1 });
  return {
    vertices: Float32Array.from(m.vertices),
    normals: Float32Array.from(m.normals),
    triangles: Uint32Array.from(m.triangles),
  };
}

export function exportSTL(shape: Shape3D, tolerance: number): Blob {
  return shape.blobSTL({ tolerance, angularTolerance: 0.2, binary: true });
}

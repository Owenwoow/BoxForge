/**
 * Recursive BSP-tree divider walls.
 *
 * Walks the validated partition tree and produces every divider wall as a
 * solid, plus a flat list of "wall specs" describing each wall's own
 * rectangular face -- hollow.ts uses those to punch vents into individual
 * dividers without re-deriving their geometry.
 *
 * The inner cavity footprint is the box's XY extent inset by `wall` on every
 * side; its floor sits at Z=wall (on top of the bottom slab).
 */
import { makeBox, type Shape3D } from "replicad";
import type { BoxConfig, PartitionNode } from "../config";

export interface WallSpec {
  axis: "x" | "y";
  /** Wall mid-plane position along its axis (world X for "x", world Y for "y"). */
  center: number;
  thickness: number;
  /** Extent along the wall's length (world Y for "x" walls, world X for "y"). */
  span0: number;
  span1: number;
  z0: number;
  z1: number;
}

interface Region {
  x0: number;
  x1: number;
  y0: number;
  y1: number;
}

function walk(
  node: PartitionNode | null,
  region: Region,
  floorZ: number,
  ceilingZ: number,
  walls: Shape3D[],
  specs: WallSpec[],
): void {
  if (!node) return;
  const { axis, at, thickness, height } = node.split;
  const z0 = floorZ;
  const z1 = height === null ? ceilingZ : Math.min(floorZ + height, ceilingZ);

  let subA: Region;
  let subB: Region;
  if (axis === "x") {
    const center = region.x0 + at;
    const a = center - thickness / 2;
    const b = center + thickness / 2;
    walls.push(makeBox([a, region.y0, z0], [b, region.y1, z1]));
    specs.push({ axis, center, thickness, span0: region.y0, span1: region.y1, z0, z1 });
    subA = { ...region, x1: a };
    subB = { ...region, x0: b };
  } else {
    const center = region.y0 + at;
    const a = center - thickness / 2;
    const b = center + thickness / 2;
    walls.push(makeBox([region.x0, a, z0], [region.x1, b, z1]));
    specs.push({ axis, center, thickness, span0: region.x0, span1: region.x1, z0, z1 });
    subA = { ...region, y1: a };
    subB = { ...region, y0: b };
  }
  walk(node.children[0], subA, floorZ, ceilingZ, walls, specs);
  walk(node.children[1], subB, floorZ, ceilingZ, walls, specs);
}

/** Returns every divider wall solid (not yet fused) and their specs. */
export function buildPartitions(tree: PartitionNode | null, box: BoxConfig): { walls: Shape3D[]; specs: WallSpec[] } {
  const walls: Shape3D[] = [];
  const specs: WallSpec[] = [];
  const hx = box.length / 2 - box.wall;
  const hy = box.width / 2 - box.wall;
  walk(tree, { x0: -hx, x1: hx, y0: -hy, y1: hy }, box.wall, box.height, walls, specs);
  return { walls, specs };
}

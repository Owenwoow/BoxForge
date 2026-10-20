/**
 * 45-degree pill-hole vent arrays.
 *
 * Fixed at 45 degrees for support-free bridging; only hole_size is exposed,
 * spacing/border are derived. Never applied to outer walls -- only to the
 * bottom slab and/or the dividers, whose exact rectangles we already know.
 */
import { draw, drawRectangle, makeCompound, type PlaneName, type Shape3D } from "replicad";
import type { BoxConfig, HollowConfig } from "../config";
import type { WallSpec } from "./partitions";

export const PILL_LENGTH_RATIO = 2.5; // pill length = hole_size * ratio
export const MIN_GAP = 0.8; // minimum bridge wall left between adjacent holes
const EPS = 0.5; // extra cut margin so booleans always fully perforate

function rotatedHalfExtents(length: number, diameter: number, angleDeg: number): [number, number] {
  const t = (angleDeg * Math.PI) / 180;
  const hl = length / 2;
  const hd = diameter / 2;
  return [hl * Math.abs(Math.cos(t)) + hd * Math.abs(Math.sin(t)), hl * Math.abs(Math.sin(t)) + hd * Math.abs(Math.cos(t))];
}

export function pillGridParams(holeSize: number, angle: number) {
  const pillLength = holeSize * PILL_LENGTH_RATIO;
  const gap = Math.max(holeSize * 0.4, MIN_GAP);
  const [halfX, halfY] = rotatedHalfExtents(pillLength, holeSize, angle);
  return {
    pillLength,
    spacingAxial: pillLength + gap, // along the pill axis: full length + bridge
    spacingPerp: holeSize + gap, // across the pill axis: width + bridge
    halfX,
    halfY,
  };
}

/**
 * Pill centers on a staggered grid rotated by `angle`. Alternate rows are
 * offset by half the axial pitch (brick pattern). Any pill that OVERLAPS the
 * area is kept: the cutter is clipped to the area afterwards, so edge pills
 * end as partial capsules at the frame instead of disappearing.
 */
export function pillCenters(
  minU: number,
  maxU: number,
  minV: number,
  maxV: number,
  holeSize: number,
  angle: number,
): [number, number][] {
  const { spacingAxial, spacingPerp, halfX, halfY } = pillGridParams(holeSize, angle);
  if (maxU - minU <= 2 * halfX || maxV - minV <= 2 * halfY) return [];
  const cu = (minU + maxU) / 2;
  const cv = (minV + maxV) / 2;
  const diag = Math.hypot(maxU - minU, maxV - minV);
  const nAxial = Math.floor(diag / (2 * spacingAxial)) + 2;
  const nPerp = Math.floor(diag / (2 * spacingPerp)) + 2;
  const t = (angle * Math.PI) / 180;
  const cos = Math.cos(t);
  const sin = Math.sin(t);

  const centers: [number, number][] = [];
  for (let j = -nPerp; j <= nPerp; j++) {
    const q = j * spacingPerp;
    const rowOffset = j % 2 !== 0 ? spacingAxial / 2 : 0;
    for (let i = -nAxial; i <= nAxial; i++) {
      const p = i * spacingAxial + rowOffset;
      const u = cu + p * cos - q * sin;
      const v = cv + p * sin + q * cos;
      if (u >= minU - halfX && u <= maxU + halfX && v >= minV - halfY && v <= maxV + halfY) {
        centers.push([u, v]);
      }
    }
  }
  return centers;
}

/** Stadium (slot) of end-to-end `length` and `diameter`, centered at the origin along +U. */
function pill(length: number, diameter: number) {
  const r = diameter / 2;
  const a = (length - diameter) / 2;
  return draw([-a, -r]).hLine(2 * a).sagittaArc(0, 2 * r, -r).hLine(-2 * a).sagittaArc(0, -2 * r, -r).close();
}

/**
 * Vent cutter for one rectangular face lying on `plane` at `offset` along its
 * normal, spanning [minU,maxU]x[minV,maxV] in the plane's local coords and
 * `thickness` deep (centered on the plane). Returns null if nothing fits.
 */
function buildCutter(
  plane: PlaneName,
  offset: number,
  minU: number,
  maxU: number,
  minV: number,
  maxV: number,
  thickness: number,
  hollow: HollowConfig,
): Shape3D | null {
  const { hole_size: holeSize, angle, border } = hollow;
  const u0 = minU + border;
  const u1 = maxU - border;
  const v0 = minV + border;
  const v1 = maxV - border;

  const centers = pillCenters(u0, u1, v0, v1, holeSize, angle);
  if (centers.length === 0) return null;

  const { pillLength } = pillGridParams(holeSize, angle);
  const depth = thickness / 2 + EPS;
  const base = pill(pillLength, holeSize).rotate(angle, [0, 0]);
  const pills = centers.map(([u, v]) => base.translate(u, v).sketchOnPlane(plane, offset - depth).extrude(2 * depth) as Shape3D);
  const cutter = makeCompound(pills) as Shape3D;

  // Clip the array to the border-inset area so frame-crossing pills get cut
  // off at the frame (partial capsules) instead of poking outside it.
  const clipDepth = depth + EPS;
  const clip = drawRectangle(u1 - u0, v1 - v0)
    .translate((u0 + u1) / 2, (v0 + v1) / 2)
    .sketchOnPlane(plane, offset - clipDepth)
    .extrude(2 * clipDepth) as Shape3D;
  return cutter.intersect(clip);
}

export function applyHollow(solid: Shape3D, box: BoxConfig, specs: WallSpec[], hollow: HollowConfig): Shape3D {
  const cutters: Shape3D[] = [];

  if (hollow.faces.bottom) {
    const hx = box.length / 2 - box.wall;
    const hy = box.width / 2 - box.wall;
    const c = buildCutter("XY", box.wall / 2, -hx, hx, -hy, hy, box.wall, hollow);
    if (c) cutters.push(c);
  }

  if (hollow.faces.partitions) {
    for (const s of specs) {
      // "x" walls lie in a YZ plane (local u = world Y, v = world Z);
      // "y" walls lie in a ZX plane (local u = world Z, v = world X).
      const c =
        s.axis === "x"
          ? buildCutter("YZ", s.center, s.span0, s.span1, s.z0, s.z1, s.thickness, hollow)
          : buildCutter("ZX", s.center, s.z0, s.z1, s.span0, s.span1, s.thickness, hollow);
      if (c) cutters.push(c);
    }
  }

  // One boolean against every cutter at once is much faster than one per face.
  if (cutters.length === 0) return solid;
  return solid.cut(cutters.length === 1 ? cutters[0] : (makeCompound(cutters) as Shape3D));
}

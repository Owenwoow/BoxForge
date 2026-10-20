/**
 * Box config schema + validation. A faithful port of box_builder/validate.py:
 * turns a raw (YAML-shaped, snake_case) config into a validated, clamped
 * config that the geometry code can consume without re-checking bounds.
 *
 * Hard failures throw ConfigError; soft fixes (clamping) are reported as
 * warnings instead of being printed, so the UI can show them.
 */

export const MAX_PLATE_XY = 250; // printer bed is 256x256, 6mm safety margin
export const DEFAULT_Z_MAX = 250;

// Abuse / resource guards: the partition tree can be pasted as free-form YAML,
// and every node is an expensive CAD boolean. Depth 8 already allows 256 cells.
export const MAX_PARTITION_DEPTH = 8;
export const MAX_PARTITION_NODES = 200;

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

// ---- Raw (user-facing / YAML) shapes -------------------------------------

export type SplitAt = number | string; // fraction 0..1, absolute mm, or "30mm"

export interface RawSplit {
  axis: "x" | "y";
  at?: SplitAt;
  thickness?: number;
  height?: number | null;
}

export interface RawPartitionNode {
  split: RawSplit;
  children?: [RawPartitionNode | null, RawPartitionNode | null];
}

export interface RawConfig {
  box: {
    size: [number, number, number];
    wall?: number;
    corner_radius?: number;
    z_max?: number;
    edge_fillet?: { top?: number; bottom?: number };
  };
  partitions?: RawPartitionNode | null;
  hollow?: {
    hole_size?: number;
    angle?: number;
    border?: number | "auto";
    faces?: { bottom?: boolean; partitions?: boolean };
  };
  export?: { format?: string; tolerance?: number; filename?: string };
}

// ---- Validated shapes ----------------------------------------------------

export interface BoxConfig {
  length: number;
  width: number;
  height: number;
  wall: number;
  corner_radius: number;
  edge_fillet: { top: number; bottom: number };
}

export interface PartitionNode {
  split: { axis: "x" | "y"; at: number; thickness: number; height: number | null };
  children: [PartitionNode | null, PartitionNode | null];
}

export interface HollowConfig {
  hole_size: number;
  angle: number;
  border: number;
  faces: { bottom: boolean; partitions: boolean };
}

export interface ExportConfig {
  format: "stl";
  tolerance: number;
  filename: string;
}

export interface Config {
  box: BoxConfig;
  partitions: PartitionNode | null;
  hollow: HollowConfig;
  export: ExportConfig;
}

export interface ValidationResult {
  config: Config;
  warnings: string[];
}

// ---- Helpers --------------------------------------------------------------

/** Python float(): accepts numbers and numeric strings, rejects the rest. */
function num(value: unknown, field: string): number {
  const n = typeof value === "string" && value.trim() !== "" ? Number(value) : value;
  if (typeof n !== "number" || !Number.isFinite(n)) {
    throw new ConfigError(`${field} must be a number, got ${JSON.stringify(value)}`);
  }
  return n;
}

const fmt3 = (n: number) => n.toFixed(3);

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

// ---- Sections -------------------------------------------------------------

function validateBox(rawBox: unknown, warn: (m: string) => void): BoxConfig {
  if (!isRecord(rawBox)) throw new ConfigError("box must be a mapping");
  const size = rawBox.size;
  if (!Array.isArray(size) || size.length !== 3) {
    throw new ConfigError("box.size must be a [length, width, height] triple");
  }
  const [length, width, height] = size.map((v, i) => num(v, `box.size[${i}]`));

  if (length <= 0 || width <= 0 || height <= 0) {
    throw new ConfigError("box.size values must all be positive");
  }
  if (length > MAX_PLATE_XY || width > MAX_PLATE_XY) {
    throw new ConfigError(
      `box length/width must be <= ${MAX_PLATE_XY}mm to fit the 256x256 print bed with safety margin (got ${length} x ${width})`,
    );
  }
  const zMax = num(rawBox.z_max ?? DEFAULT_Z_MAX, "box.z_max");
  if (height > zMax) throw new ConfigError(`box height ${height} exceeds z_max ${zMax}`);

  const wall = num(rawBox.wall ?? 2, "box.wall");
  if (wall <= 0) throw new ConfigError("box.wall must be positive");
  if (wall * 2 >= Math.min(length, width)) {
    throw new ConfigError("box.wall is too thick for the given length/width");
  }

  let cornerRadius = num(rawBox.corner_radius ?? 0, "box.corner_radius");
  const maxCorner = (Math.min(length, width) / 2) * 0.9;
  if (cornerRadius < 0) throw new ConfigError("box.corner_radius must be >= 0");
  if (cornerRadius > maxCorner) {
    warn(`corner_radius ${cornerRadius} exceeds geometric limit ${fmt3(maxCorner)}, clamping`);
    cornerRadius = Math.max(maxCorner, 0);
  }

  const ef = isRecord(rawBox.edge_fillet) ? rawBox.edge_fillet : {};
  let top = num(ef.top ?? 0, "edge_fillet.top");
  let bottom = num(ef.bottom ?? 0, "edge_fillet.bottom");
  if (top < 0 || bottom < 0) throw new ConfigError("edge_fillet values must be >= 0");

  // The top rim fillet rounds the outer AND inner rim edge at once; they meet
  // (and OCCT fails) once the radius reaches wall/2. Keep a safety margin.
  const maxTop = (wall / 2) * 0.9;
  if (top > maxTop) {
    warn(`edge_fillet.top ${top} exceeds safe limit, clamping to ${fmt3(maxTop)}`);
    top = Math.max(maxTop, 0);
  }
  const maxBottom = Math.min(height, Math.min(length, width) / 2) * 0.8;
  if (bottom > maxBottom) {
    warn(`edge_fillet.bottom ${bottom} exceeds safe limit, clamping to ${fmt3(maxBottom)}`);
    bottom = Math.max(maxBottom, 0);
  }

  return { length, width, height, wall, corner_radius: cornerRadius, edge_fillet: { top, bottom } };
}

/** Resolve a split position (fraction, mm number, or "Nmm") to an absolute mm offset. */
export function resolveSplitAt(at: unknown, span: number): number {
  if (typeof at === "string") {
    const s = at.trim().toLowerCase();
    if (!s.endsWith("mm")) {
      throw new ConfigError(`partition 'at' string must end in 'mm', got ${JSON.stringify(at)}`);
    }
    return num(s.slice(0, -2), "partition at");
  }
  const n = num(at, "partition at");
  return n >= 0 && n <= 1 ? n * span : n;
}

function validatePartitionNode(
  node: unknown,
  spanX: number,
  spanY: number,
  wall: number,
  boxHeight: number,
  depth: number,
  counter: { n: number },
): PartitionNode | null {
  if (node === null || node === undefined) return null;
  if (depth > MAX_PARTITION_DEPTH) {
    throw new ConfigError(`partition tree too deep (max nesting ${MAX_PARTITION_DEPTH})`);
  }
  counter.n += 1;
  if (counter.n > MAX_PARTITION_NODES) {
    throw new ConfigError(`too many partition dividers (max ${MAX_PARTITION_NODES})`);
  }
  if (!isRecord(node)) throw new ConfigError("partition node must be a mapping or null");
  const split = node.split;
  if (!isRecord(split)) throw new ConfigError("partition node must have a 'split' key (or be null)");

  const axis = split.axis;
  if (axis !== "x" && axis !== "y") {
    throw new ConfigError(`partition split.axis must be 'x' or 'y', got ${JSON.stringify(axis)}`);
  }
  const span = axis === "x" ? spanX : spanY;

  const thickness = num(split.thickness ?? wall, "partition split.thickness");
  if (thickness <= 0) throw new ConfigError("partition split.thickness must be positive");

  const at = resolveSplitAt(split.at ?? 0.5, span);
  if (at - thickness / 2 <= 0 || at + thickness / 2 >= span) {
    throw new ConfigError(
      `partition split at=${at} thickness=${thickness} does not fit within span ${span} on axis ${axis}`,
    );
  }

  let height: number | null = null;
  if (split.height !== null && split.height !== undefined) {
    height = num(split.height, "partition split.height");
    if (height <= 0 || height > boxHeight) {
      throw new ConfigError(`partition split.height ${height} out of range (0, ${boxHeight}]`);
    }
  }

  const childrenRaw = node.children ?? [null, null];
  if (!Array.isArray(childrenRaw) || childrenRaw.length !== 2) {
    throw new ConfigError("partition node.children must have exactly 2 entries");
  }

  const spanA = at - thickness / 2;
  let childA: PartitionNode | null;
  let childB: PartitionNode | null;
  if (axis === "x") {
    const spanB = spanX - at - thickness / 2;
    childA = validatePartitionNode(childrenRaw[0], spanA, spanY, wall, boxHeight, depth + 1, counter);
    childB = validatePartitionNode(childrenRaw[1], spanB, spanY, wall, boxHeight, depth + 1, counter);
  } else {
    const spanB = spanY - at - thickness / 2;
    childA = validatePartitionNode(childrenRaw[0], spanX, spanA, wall, boxHeight, depth + 1, counter);
    childB = validatePartitionNode(childrenRaw[1], spanX, spanB, wall, boxHeight, depth + 1, counter);
  }

  return { split: { axis, at, thickness, height }, children: [childA, childB] };
}

function validateHollow(rawHollow: unknown, box: BoxConfig, warn: (m: string) => void): HollowConfig {
  const h = isRecord(rawHollow) ? rawHollow : {};
  const holeSize = num(h.hole_size ?? 8, "hollow.hole_size");
  if (holeSize <= 0) throw new ConfigError("hollow.hole_size must be positive");

  let angle = num(h.angle ?? 45, "hollow.angle");
  if (angle !== 45) {
    warn("hollow.angle forced to 45 (fixed for support-free printing)");
    angle = 45;
  }

  let border: number;
  if (h.border === undefined || h.border === "auto") {
    border = Math.max(box.wall, holeSize * 0.5);
  } else {
    border = num(h.border, "hollow.border");
    if (border < 0) throw new ConfigError("hollow.border must be >= 0");
  }

  const faces = isRecord(h.faces) ? h.faces : {};
  return {
    hole_size: holeSize,
    angle,
    border,
    faces: { bottom: Boolean(faces.bottom), partitions: Boolean(faces.partitions) },
  };
}

function validateExport(rawExport: unknown): ExportConfig {
  const e = isRecord(rawExport) ? rawExport : {};
  const format = e.format ?? "stl";
  if (format !== "stl") {
    throw new ConfigError(`only 'stl' export format is supported, got ${JSON.stringify(format)}`);
  }
  const tolerance = num(e.tolerance ?? 0.1, "export.tolerance");
  if (tolerance <= 0) throw new ConfigError("export.tolerance must be positive");
  return { format: "stl", tolerance, filename: sanitizeFilename(e.filename ?? "box_output.stl") };
}

/**
 * Reduce a user-supplied export filename to a safe bare basename: no
 * directory component, only a small safe character set, always ".stl".
 */
export function sanitizeFilename(raw: unknown): string {
  let name = String(raw ?? "").trim().replace(/\\/g, "/");
  name = name.slice(name.lastIndexOf("/") + 1);
  name = name.replace(/[^A-Za-z0-9._\- ]+/g, "_");
  name = name.replace(/^[. ]+|[. ]+$/g, "");
  if (!name) name = "box_output.stl";
  if (!name.toLowerCase().endsWith(".stl")) name += ".stl";
  return name;
}

export function validateConfig(raw: unknown): ValidationResult {
  if (!isRecord(raw) || !("box" in raw)) {
    throw new ConfigError("config must have a top-level 'box' section");
  }
  const warnings: string[] = [];
  const warn = (m: string) => warnings.push(m);

  const box = validateBox(raw.box, warn);
  const partitions = validatePartitionNode(
    raw.partitions,
    box.length - 2 * box.wall,
    box.width - 2 * box.wall,
    box.wall,
    box.height,
    0,
    { n: 0 },
  );
  const hollow = validateHollow(raw.hollow, box, warn);
  const exportCfg = validateExport(raw.export);

  return { config: { box, partitions, hollow, export: exportCfg }, warnings };
}

// ---- Defaults & presets (shared by the UI and tests) ------------------------

/** The same sample as box_generator/config.yaml. */
export const SAMPLE_CONFIG: RawConfig = {
  box: { size: [120, 80, 40], wall: 2, corner_radius: 8, edge_fillet: { top: 1, bottom: 1 } },
  partitions: {
    split: { axis: "x", at: 0.5, thickness: 1.5, height: null },
    children: [
      { split: { axis: "y", at: "30mm", thickness: 1.5, height: null }, children: [null, null] },
      null,
    ],
  },
  hollow: { hole_size: 8, angle: 45, border: "auto", faces: { bottom: true, partitions: true } },
  export: { format: "stl", tolerance: 0.1, filename: "box_output.stl" },
};

export function splitNode(axis: "x" | "y", at: number, thickness: number): RawPartitionNode {
  return { split: { axis, at, thickness, height: null }, children: [null, null] };
}

export type PresetId = "none" | "half_cols" | "half_rows" | "cross";

export const PRESETS: Record<PresetId, (thickness: number) => RawPartitionNode | null> = {
  none: () => null,
  half_cols: (t) => splitNode("x", 0.5, t),
  half_rows: (t) => splitNode("y", 0.5, t),
  cross: (t) => ({ ...splitNode("x", 0.5, t), children: [splitNode("y", 0.5, t), splitNode("y", 0.5, t)] }),
};

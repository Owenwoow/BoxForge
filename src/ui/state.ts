/**
 * Editor state <-> raw config. The editor keeps flat fields for the form
 * controls; `toRawConfig` produces the same YAML-shaped config the original
 * CLI used, so configs can be exported, imported and shared by link.
 */
import type { RawConfig, RawPartitionNode } from "../core/config";

export interface EditorState {
  length: number;
  width: number;
  height: number;
  wall: number;
  cornerRadius: number;
  edgeTop: number;
  edgeBottom: number;
  tree: RawPartitionNode | null;
  holeSize: number;
  borderAuto: boolean;
  border: number;
  ventBottom: boolean;
  ventPartitions: boolean;
  tolerance: number;
  filename: string;
}

export const DEFAULT_STATE: EditorState = {
  length: 120,
  width: 80,
  height: 40,
  wall: 2,
  cornerRadius: 5,
  edgeTop: 0.5,
  edgeBottom: 1,
  tree: null,
  holeSize: 8,
  borderAuto: true,
  border: 3,
  ventBottom: false,
  ventPartitions: false,
  tolerance: 0.1,
  filename: "box_output.stl",
};

export const TOLERANCES = [0.5, 0.2, 0.1, 0.05, 0.02];

export function toRawConfig(s: EditorState): RawConfig {
  return {
    box: {
      size: [s.length, s.width, s.height],
      wall: s.wall,
      corner_radius: s.cornerRadius,
      edge_fillet: { top: s.edgeTop, bottom: s.edgeBottom },
    },
    partitions: s.tree,
    hollow: {
      hole_size: s.holeSize,
      angle: 45,
      border: s.borderAuto ? "auto" : s.border,
      faces: { bottom: s.ventBottom, partitions: s.ventPartitions },
    },
    export: { format: "stl", tolerance: s.tolerance, filename: s.filename },
  };
}

const n = (v: unknown, fallback: number) => (typeof v === "number" && Number.isFinite(v) ? v : fallback);

/** Best-effort import: unknown/missing fields fall back to defaults; validation happens at build time. */
export function fromRawConfig(raw: unknown): EditorState {
  const r = (raw ?? {}) as Partial<RawConfig>;
  const d = DEFAULT_STATE;
  const size = Array.isArray(r.box?.size) ? r.box!.size : [];
  const border = r.hollow?.border;
  return {
    length: n(size[0], d.length),
    width: n(size[1], d.width),
    height: n(size[2], d.height),
    wall: n(r.box?.wall, d.wall),
    cornerRadius: n(r.box?.corner_radius, 0),
    edgeTop: n(r.box?.edge_fillet?.top, 0),
    edgeBottom: n(r.box?.edge_fillet?.bottom, 0),
    tree: (r.partitions as RawPartitionNode | null | undefined) ?? null,
    holeSize: n(r.hollow?.hole_size, d.holeSize),
    borderAuto: border === undefined || border === "auto",
    border: n(border, d.border),
    ventBottom: Boolean(r.hollow?.faces?.bottom),
    ventPartitions: Boolean(r.hollow?.faces?.partitions),
    tolerance: n(r.export?.tolerance, d.tolerance),
    filename: typeof r.export?.filename === "string" ? r.export.filename : d.filename,
  };
}

// ---- Share links: the config travels in the URL hash, no server needed ----

export function encodeShare(s: EditorState): string {
  const bytes = new TextEncoder().encode(JSON.stringify(toRawConfig(s)));
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function decodeShare(hash: string): EditorState | null {
  const m = /(?:^#|&)c=([A-Za-z0-9_-]+)/.exec(hash);
  if (!m) return null;
  try {
    const bin = atob(m[1].replace(/-/g, "+").replace(/_/g, "/"));
    const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    return fromRawConfig(JSON.parse(new TextDecoder().decode(bytes)));
  } catch {
    return null;
  }
}

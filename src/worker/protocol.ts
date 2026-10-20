/** Messages between the UI thread and the modeling worker. */
import type { ModelStats, PreviewMesh } from "../core/geometry/build";

export type ToWorker =
  | { type: "build"; id: number; raw: unknown }
  | { type: "export"; id: number; tolerance: number };

export type FromWorker =
  | { type: "ready" }
  | { type: "fatal"; message: string }
  | { type: "built"; id: number; stats: ModelStats; warnings: string[]; mesh: PreviewMesh; ms: number }
  | { type: "failed"; id: number; kind: "config" | "model"; message: string }
  | { type: "stl"; id: number; blob: Blob }
  | { type: "stl-failed"; id: number; message: string };

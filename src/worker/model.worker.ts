/**
 * Modeling worker: owns the OpenCASCADE kernel so heavy B-rep booleans never
 * block the UI. Builds are processed one at a time; the UI only ever sends
 * the newest config, so there is no queue to drain.
 */
import wasmUrl from "replicad-opencascadejs/wasm?url";
import type { Shape3D } from "replicad";
import { ConfigError, validateConfig } from "../core/config";
import { buildModel, exportSTL, modelStats, previewMesh } from "../core/geometry/build";
import { initOC } from "../core/geometry/oc";
import type { FromWorker, ToWorker } from "./protocol";

const post = (msg: FromWorker, transfer: Transferable[] = []) => self.postMessage(msg, { transfer });

let current: Shape3D | null = null;

const errorMessage = (e: unknown) =>
  e instanceof Error ? e.message : typeof e === "number" ? `OpenCASCADE exception (${e})` : String(e);

const ready = initOC(wasmUrl).then(
  () => post({ type: "ready" }),
  (e) => post({ type: "fatal", message: errorMessage(e) }),
);

self.onmessage = async (event: MessageEvent<ToWorker>) => {
  await ready;
  const msg = event.data;

  if (msg.type === "build") {
    const t0 = performance.now();
    let config;
    let warnings: string[];
    try {
      ({ config, warnings } = validateConfig(msg.raw));
    } catch (e) {
      post({ type: "failed", id: msg.id, kind: e instanceof ConfigError ? "config" : "model", message: errorMessage(e) });
      return;
    }
    try {
      const shape = buildModel(config);
      const stats = modelStats(shape);
      const mesh = previewMesh(shape);
      current?.delete(); // free the previous model's WebAssembly memory
      current = shape;
      post(
        { type: "built", id: msg.id, stats, warnings, mesh, ms: performance.now() - t0 },
        [mesh.vertices.buffer, mesh.normals.buffer, mesh.triangles.buffer],
      );
    } catch (e) {
      post({ type: "failed", id: msg.id, kind: "model", message: errorMessage(e) });
    }
    return;
  }

  if (msg.type === "export") {
    try {
      if (!current) throw new Error("no model built yet");
      post({ type: "stl", id: msg.id, blob: exportSTL(current, msg.tolerance) });
    } catch (e) {
      post({ type: "stl-failed", id: msg.id, message: errorMessage(e) });
    }
  }
};

import { useCallback, useEffect, useRef, useState } from "react";
import type { ModelStats, PreviewMesh } from "../core/geometry/build";
import type { FromWorker, ToWorker } from "../worker/protocol";

export interface ModelState {
  kernel: "loading" | "ready" | "failed";
  fatal?: string;
  building: boolean;
  mesh: PreviewMesh | null;
  stats: ModelStats | null;
  warnings: string[];
  ms: number | null;
  error: { kind: "config" | "model"; message: string } | null;
}

/**
 * Drives the modeling worker. At most one build runs at a time; while it
 * runs, only the newest requested config is remembered, so dragging a slider
 * never piles up a backlog of stale builds.
 */
export function useModel(raw: unknown) {
  const worker = useRef<Worker | null>(null);
  const nextId = useRef(0);
  const inFlight = useRef<number | null>(null);
  const pending = useRef<unknown>(undefined);
  const exports = useRef(new Map<number, (r: { blob?: Blob; error?: string }) => void>());
  const [state, setState] = useState<ModelState>({
    kernel: "loading",
    building: false,
    mesh: null,
    stats: null,
    warnings: [],
    ms: null,
    error: null,
  });

  const send = useCallback((msg: ToWorker) => worker.current?.postMessage(msg), []);

  const startBuild = useCallback(
    (cfg: unknown) => {
      const id = ++nextId.current;
      inFlight.current = id;
      setState((s) => ({ ...s, building: true }));
      send({ type: "build", id, raw: cfg });
    },
    [send],
  );

  useEffect(() => {
    const w = new Worker(new URL("../worker/model.worker.ts", import.meta.url), { type: "module" });
    worker.current = w;
    w.onmessage = (e: MessageEvent<FromWorker>) => {
      const msg = e.data;
      switch (msg.type) {
        case "ready":
          setState((s) => ({ ...s, kernel: "ready" }));
          break;
        case "fatal":
          setState((s) => ({ ...s, kernel: "failed", fatal: msg.message }));
          break;
        case "built":
        case "failed":
          if (msg.id !== inFlight.current) break;
          inFlight.current = null;
          setState((s) =>
            msg.type === "built"
              ? { ...s, mesh: msg.mesh, stats: msg.stats, warnings: msg.warnings, ms: msg.ms, error: null }
              : { ...s, error: { kind: msg.kind, message: msg.message } },
          );
          if (pending.current !== undefined) {
            const cfg = pending.current;
            pending.current = undefined;
            startBuild(cfg);
          } else {
            setState((s) => ({ ...s, building: false }));
          }
          break;
        case "stl":
        case "stl-failed":
          exports.current.get(msg.id)?.(msg.type === "stl" ? { blob: msg.blob } : { error: msg.message });
          exports.current.delete(msg.id);
          break;
      }
    };
    w.onerror = (e) => setState((s) => ({ ...s, kernel: "failed", fatal: e.message || "worker error" }));
    return () => {
      w.terminate();
      worker.current = null;
      inFlight.current = null;
    };
  }, [startBuild]);

  // Debounce config changes a little, then build (or queue as the newest).
  useEffect(() => {
    const timer = setTimeout(() => {
      if (inFlight.current !== null) pending.current = raw;
      else startBuild(raw);
    }, 120);
    return () => clearTimeout(timer);
  }, [raw, startBuild]);

  const exportStl = useCallback(
    (tolerance: number) =>
      new Promise<Blob>((resolve, reject) => {
        const id = ++nextId.current;
        exports.current.set(id, (r) => (r.blob ? resolve(r.blob) : reject(new Error(r.error))));
        send({ type: "export", id, tolerance });
      }),
    [send],
  );

  return { ...state, exportStl };
}

/**
 * One-time OpenCASCADE (WebAssembly) kernel setup for replicad.
 *
 * In the browser the worker passes the bundled .wasm URL; in Node (tests) the
 * Emscripten loader finds the .wasm next to its own JS file.
 */
import opencascade from "replicad-opencascadejs";
import { getOC, setOC } from "replicad";

let ready: Promise<void> | null = null;

export function initOC(wasmUrl?: string): Promise<void> {
  ready ??= (async () => {
    const oc = await opencascade(wasmUrl ? { locateFile: () => wasmUrl } : undefined);
    setOC(oc);
  })();
  return ready;
}

/** Raw OpenCASCADE bindings, for the few calls replicad doesn't expose as we need. */
export const oc = () => getOC();

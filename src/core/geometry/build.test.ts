/**
 * Real OpenCASCADE geometry (WebAssembly, in Node). The reference volumes
 * were produced by the original Python/CadQuery implementation (`legacy`
 * branch) for the same configs, so these tests pin the port to it.
 */
import { beforeAll, describe, expect, it } from "vitest";
import { SAMPLE_CONFIG, validateConfig, type RawConfig } from "../config";
import { buildModel, exportSTL, modelStats, previewMesh } from "./build";
import { initOC } from "./oc";

beforeAll(() => initOC(), 60_000);

const build = (raw: RawConfig) => buildModel(validateConfig(raw).config);

const CROSS_WITH_VENTS: RawConfig = {
  box: { size: [150, 100, 50], wall: 2.4, corner_radius: 10, edge_fillet: { top: 1, bottom: 2 } },
  partitions: {
    split: { axis: "x", at: 0.5, thickness: 2 },
    children: [
      { split: { axis: "y", at: 0.5, thickness: 2 } },
      { split: { axis: "y", at: 0.5, thickness: 2, height: 25 } },
    ],
  },
  hollow: { hole_size: 6, faces: { bottom: true, partitions: true } },
};

describe("buildModel matches the CadQuery reference", () => {
  it.each([
    ["sample config", SAMPLE_CONFIG, 43848.17],
    ["plain square box", { box: { size: [100, 100, 30], wall: 2, corner_radius: 0 } } as RawConfig, 41952.0],
    ["cross dividers + partial height + vents", CROSS_WITH_VENTS, 84176.12],
  ])("%s", (_name, raw, expectedVolume) => {
    const stats = modelStats(build(raw));
    expect(stats.valid).toBe(true);
    expect(stats.volume).toBeCloseTo(expectedVolume, 0);
  });
});

describe("model output", () => {
  it("keeps the declared outer dimensions", () => {
    const stats = modelStats(build({ ...SAMPLE_CONFIG, partitions: null }));
    expect(stats.size[0]).toBeCloseTo(120, 3);
    expect(stats.size[1]).toBeCloseTo(80, 3);
    expect(stats.size[2]).toBeCloseTo(40, 3);
  });

  it("vents remove material", () => {
    const solid = modelStats(build({ ...SAMPLE_CONFIG, hollow: { faces: { bottom: false, partitions: false } } }));
    const vented = modelStats(build(SAMPLE_CONFIG));
    expect(vented.volume).toBeLessThan(solid.volume);
  });

  it("produces a preview mesh and a binary STL", async () => {
    const shape = build(SAMPLE_CONFIG);
    const mesh = previewMesh(shape);
    expect(mesh.triangles.length % 3).toBe(0);
    expect(mesh.vertices.length).toBe(mesh.normals.length);

    const stl = new Uint8Array(await exportSTL(shape, 0.1).arrayBuffer());
    const triangles = new DataView(stl.buffer).getUint32(80, true);
    expect(triangles).toBeGreaterThan(1000);
    expect(stl.byteLength).toBe(84 + 50 * triangles);
  });
});

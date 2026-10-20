import { describe, expect, it } from "vitest";
import {
  ConfigError,
  MAX_PARTITION_DEPTH,
  MAX_PARTITION_NODES,
  MAX_PLATE_XY,
  PRESETS,
  SAMPLE_CONFIG,
  sanitizeFilename,
  validateConfig,
  type RawConfig,
  type RawPartitionNode,
} from "./config";

const cfg = (box: Partial<RawConfig["box"]> = {}, rest: Partial<RawConfig> = {}): RawConfig => ({
  box: { size: [120, 80, 40], wall: 2, corner_radius: 8, edge_fillet: { top: 0.5, bottom: 1 }, ...box },
  ...rest,
});

const split = (axis: "x" | "y" = "x", at: number | string = 0.5, children: RawPartitionNode["children"] = [null, null]) =>
  ({ split: { axis, at, thickness: 1.5 }, children }) as RawPartitionNode;

const v = (raw: unknown) => validateConfig(raw).config;

describe("validateConfig", () => {
  it("fills defaults for a minimal config", () => {
    const c = v(cfg());
    expect(c.box.length).toBe(120);
    expect(c.partitions).toBeNull();
    expect(c.hollow.faces).toEqual({ bottom: false, partitions: false });
    expect(c.export).toEqual({ format: "stl", tolerance: 0.1, filename: "box_output.stl" });
  });

  it("rejects a config without a box section", () => {
    expect(() => validateConfig({})).toThrow(ConfigError);
  });

  it.each([
    [[MAX_PLATE_XY + 1, 80, 40]],
    [[80, MAX_PLATE_XY + 1, 40]],
  ])("rejects a footprint larger than the bed: %j", (size) => {
    expect(() => v(cfg({ size: size as [number, number, number] }))).toThrow(/print bed/);
  });

  it.each([[[0, 80, 40]], [[120, -1, 40]], [[120, 80]]])("rejects bad sizes: %j", (size) => {
    expect(() => v(cfg({ size: size as [number, number, number] }))).toThrow(ConfigError);
  });

  it("rejects a wall too thick for the footprint", () => {
    expect(() => v(cfg({ size: [20, 20, 20], wall: 10 }))).toThrow(/wall/);
  });

  it("clamps the corner radius to the geometric limit", () => {
    const r = validateConfig(cfg({ corner_radius: 999 }));
    expect(r.config.box.corner_radius).toBeCloseTo((80 / 2) * 0.9);
    expect(r.warnings).toHaveLength(1);
  });

  it("clamps the top fillet below half the wall", () => {
    expect(v(cfg({ edge_fillet: { top: 5, bottom: 0 } })).box.edge_fillet.top).toBeLessThan(1);
  });

  it("accepts split positions as fractions and as mm strings", () => {
    expect(v(cfg({}, { partitions: split("x", "30mm") })).partitions!.split.at).toBe(30);
    expect(v(cfg({}, { partitions: split("x", 0.25) })).partitions!.split.at).toBeCloseTo((120 - 4) * 0.25);
  });

  it("rejects a split outside its span", () => {
    expect(() => v(cfg({}, { partitions: split("x", "500mm") }))).toThrow(/does not fit/);
  });

  it("rejects an unknown axis", () => {
    expect(() => v(cfg({}, { partitions: split("z" as "x") }))).toThrow(/axis/);
  });

  it("caps the partition depth", () => {
    // Tiny mm offsets keep every split valid, so only the depth guard can stop it.
    let node: RawPartitionNode | null = null;
    for (let i = 0; i < MAX_PARTITION_DEPTH + 2; i++) node = split("x", "2mm", [null, node]);
    expect(() => v(cfg({ size: [250, 80, 40] }, { partitions: node }))).toThrow(/too deep/);
  });

  it("caps the number of dividers", () => {
    const tree = (depth: number): RawPartitionNode | null =>
      depth === 0 ? null : split(depth % 2 ? "x" : "y", 0.5, [tree(depth - 1), tree(depth - 1)]);
    expect(2 ** MAX_PARTITION_DEPTH - 1).toBeGreaterThan(MAX_PARTITION_NODES);
    expect(() => v(cfg({ size: [250, 250, 40] }, { partitions: tree(MAX_PARTITION_DEPTH) }))).toThrow(/too many/);
  });

  it("forces the vent angle to 45", () => {
    const r = validateConfig(cfg({}, { hollow: { angle: 30 } }));
    expect(r.config.hollow.angle).toBe(45);
    expect(r.warnings[0]).toMatch(/45/);
  });

  it("derives the auto vent border", () => {
    expect(v(cfg({}, { hollow: { hole_size: 8 } })).hollow.border).toBe(4);
    expect(v(cfg({ wall: 5 }, { hollow: { hole_size: 8 } })).hollow.border).toBe(5);
  });

  it("only supports STL export", () => {
    expect(() => v(cfg({}, { export: { format: "step" } }))).toThrow(/stl/);
  });

  it("accepts the sample config and every preset", () => {
    expect(() => v(SAMPLE_CONFIG)).not.toThrow();
    for (const build of Object.values(PRESETS)) {
      expect(() => v(cfg({}, { partitions: build(2) }))).not.toThrow();
    }
  });
});

describe("sanitizeFilename", () => {
  it.each([
    ["box.stl", "box.stl"],
    ["my box", "my box.stl"],
    ["../../etc/passwd", "passwd.stl"],
    ["C:\\Windows\\evil.stl", "evil.stl"],
    ["/abs/path/x.STL", "x.STL"],
    ["a$b|c.stl", "a_b_c.stl"],
    ["..", "box_output.stl"],
    ["", "box_output.stl"],
    [null, "box_output.stl"],
  ])("%j -> %j", (raw, expected) => {
    expect(sanitizeFilename(raw)).toBe(expected);
  });
});

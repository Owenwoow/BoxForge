import { describe, expect, it } from "vitest";
import { SAMPLE_CONFIG, validateConfig } from "../core/config";
import { DEFAULT_STATE, decodeShare, encodeShare, fromRawConfig, toRawConfig } from "./state";

describe("editor state", () => {
  it("default state produces a valid config", () => {
    expect(() => validateConfig(toRawConfig(DEFAULT_STATE))).not.toThrow();
  });

  it("round-trips the sample (CLI) config", () => {
    expect(toRawConfig(fromRawConfig(SAMPLE_CONFIG))).toEqual(SAMPLE_CONFIG);
  });

  it("falls back to defaults for junk input", () => {
    expect(fromRawConfig("not a config").length).toBe(DEFAULT_STATE.length);
    expect(fromRawConfig(null).tree).toBeNull();
  });

  it("round-trips through a share link, including non-ASCII filenames", () => {
    const s = { ...fromRawConfig(SAMPLE_CONFIG), filename: "收纳盒.stl" };
    expect(decodeShare(`#c=${encodeShare(s)}`)).toEqual(s);
  });

  it("ignores missing or corrupt share links", () => {
    expect(decodeShare("")).toBeNull();
    expect(decodeShare("#c=%%%")).toBeNull();
    expect(decodeShare("#c=bm90LWpzb24")).toBeNull();
  });
});

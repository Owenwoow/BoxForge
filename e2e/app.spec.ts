import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";
import { DEFAULT_STATE, encodeShare } from "../src/ui/state";

test("builds the default box and downloads a valid STL", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByTestId("valid")).toHaveText("OK", { timeout: 90_000 });

  const download = page.getByRole("button", { name: /下载 STL|Download STL/ });
  await expect(download).toBeEnabled();
  const [file] = await Promise.all([page.waitForEvent("download"), download.click()]);
  expect(file.suggestedFilename()).toBe("box_output.stl");

  const stl = await readFile(await file.path());
  const triangles = stl.readUInt32LE(80);
  expect(triangles).toBeGreaterThan(1000);
  expect(stl.length).toBe(84 + 50 * triangles);
});

test("loads a shared design from the link and rebuilds on edits", async ({ page }) => {
  const shared = { ...DEFAULT_STATE, length: 150, tree: { split: { axis: "x" as const, at: 0.5, thickness: 2 } } };
  await page.goto(`./#c=${encodeShare(shared)}`);
  await expect(page.getByTestId("valid")).toHaveText("OK", { timeout: 90_000 });
  await expect(page.getByTestId("metrics")).toContainText("150.0");

  await page.getByRole("spinbutton", { name: /^宽|^Width/ }).fill("100");
  await page.getByRole("spinbutton", { name: /^宽|^Width/ }).press("Enter");
  await expect(page.getByTestId("metrics")).toContainText("150.0 × 100.0");
});

test("reports an invalid config instead of crashing", async ({ page }) => {
  const bad = { ...DEFAULT_STATE, tree: { split: { axis: "x" as const, at: "500mm", thickness: 2 } } };
  await page.goto(`./#c=${encodeShare(bad)}`);
  await expect(page.getByTestId("model-error")).toContainText("does not fit", { timeout: 90_000 });
  await expect(page.getByRole("button", { name: /下载 STL|Download STL/ })).toBeDisabled();
});

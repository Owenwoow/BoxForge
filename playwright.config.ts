import { defineConfig, devices } from "@playwright/test";

// End-to-end check of the production build: the real WebAssembly kernel,
// worker and 3D view in a real browser, exactly as GitHub Pages serves it.
export default defineConfig({
  testDir: "e2e",
  timeout: 120_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://localhost:4173/",
    locale: "zh-CN",
    trace: "retain-on-failure",
  },
  // CI uses Playwright's bundled Chromium; PW_CHANNEL=chrome reuses a locally installed Chrome.
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], channel: process.env.PW_CHANNEL } }],
  webServer: {
    command: "npm run preview",
    url: "http://localhost:4173/",
    reuseExistingServer: !process.env.CI,
  },
});

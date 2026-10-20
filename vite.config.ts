/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // Relative asset URLs: the same build works at https://<user>.github.io/BoxForge/
  // (GitHub Pages project site), at a custom domain root, or from `vite preview`.
  base: "./",
  plugins: [react()],
  worker: { format: "es" },
  build: {
    target: "es2022",
    // The OpenCASCADE kernel is a single ~22 MB .wasm asset; that's expected.
    chunkSizeWarningLimit: 2048,
  },
  test: {
    include: ["src/**/*.test.ts"],
    // Real B-rep modeling in WebAssembly: a full model can take a few seconds.
    testTimeout: 60_000,
  },
});

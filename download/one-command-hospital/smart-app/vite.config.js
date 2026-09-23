import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Stop PostCSS config lookup from walking up into the parent Next.js project.
  css: { postcss: { plugins: [] } },
  // Served into the EHR iframe via SMART launch; path stays relative so it
  // works behind proxies (OpenEMR, Medplum, or a hospital reverse proxy).
  base: "./",
  build: { outDir: "dist" },
});

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["react/**/*.test.tsx"],
    setupFiles: ["./react/test-setup.ts"],
  },
});

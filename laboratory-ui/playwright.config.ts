import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: process.env.LAB_URL || "http://127.0.0.1:8765",
    channel: process.env.PLAYWRIGHT_CHANNEL,
    headless: true,
    viewport: { width: 1440, height: 1100 },
  },
  workers: 1,
});

import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  retries: process.env.CI ? 2 : 1,
  outputDir: "test-results",
  reporter: [["list"], ["./src/bug-report-reporter.ts"]],
  use: {
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});

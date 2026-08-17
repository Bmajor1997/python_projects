import { defineConfig } from "@playwright/test";
export default defineConfig({
    testDir: "./tests",
    retries: 1,
    outputDir: "test-results",

    reporter: [
        ["list"],
    ],

    use: {
        screenshot: "only-on-failure",
        trace: "retain-on-failure",
        video: "retain-on-failure",
    },
    
    projects: [
  {
    name: "chromium",
    use: {
      browserName: "chromium",
    },
  },
],
});
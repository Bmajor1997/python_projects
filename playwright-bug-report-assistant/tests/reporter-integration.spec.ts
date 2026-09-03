import { expect, test } from "@playwright/test";
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import type { TestCase, TestResult } from "@playwright/test/reporter";
import BugReportReporter from "../src/bug-report-reporter";

test("the reporter converts a failed result into JSON and Markdown", async () => {
  const reporter = new BugReportReporter();
  const uniqueTitle = `synthetic reporter failure ${Date.now()}`;
  const testCase = {
    titlePath: () => [uniqueTitle],
    location: { file: join(process.cwd(), "tests", "reporter-integration.spec.ts"), line: 9, column: 1 },
    expectedStatus: "passed",
    tags: [],
    parent: { project: () => ({ name: "integration", use: { browserName: "chromium", viewport: { width: 1280, height: 720 } } }) },
  } as unknown as TestCase;
  const result = {
    status: "failed", errors: [{ message: "Timeout waiting for Complete purchase", stack: `at checkout (${join(process.cwd(), "tests", "reporter-integration.spec.ts")}:9:1)` }],
    attachments: [], steps: [], startTime: new Date(), duration: 100, retry: 0,
  } as unknown as TestResult;
  reporter.onTestEnd(testCase, result);
  await reporter.onEnd();
  const outputRoot = join(process.cwd(), "test-results", "failure-analyses");
  const directory = (await readdir(outputRoot)).find(name => name.startsWith("synthetic-reporter-failure"));
  expect(directory).toBeTruthy();
  const reportDirectory = join(outputRoot, directory!);
  const files = await readdir(reportDirectory);
  expect(files).toEqual(expect.arrayContaining(["failure-analysis.json", "failure-summary.md", "evidence"]));
  expect(await readFile(join(reportDirectory, "failure-summary.md"), "utf8")).toContain("Analysis provider");
});

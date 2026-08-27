import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { format_failure_summary, normalize_failure_analysis_data } from "../src/failure-output";
import { make_failure_analysis_folder_name, read_failure_analysis_data, save_failure_analysis } from "../src/report-bundle";
import type { FailureAnalysisData } from "../src/types";

function analysis(mode: FailureAnalysisData["mode"] = "developer"): FailureAnalysisData {
  return {
    details: { testTitle: "Checkout <script>alert(1)</script>", testFile: "tests/checkout.spec.ts", lineNumber: 4, columnNumber: 2, status: "failed", errorMessage: "Expected <paid> Bearer abcdefghijklmnop", stackTrace: "Error <unsafe>", startTime: new Date("2026-08-25T12:00:00Z"), durationMs: 50, retryNumber: 0, testSteps: ["Submit <payment>"], expectedBehavior: "Receipt <shown>", actualBehavior: "Error <shown>", failedStep: "Submit <payment>", tags: [] },
    evidence: { screenshotPaths: [], tracePaths: [], otherAttachments: [], currentUrl: "https://shop.test/?token=secret", consoleMessages: ["console <secret>"], pageErrors: ["page <secret>"], networkFailures: [{ method: "GET", url: "https://api.test/<private>", status: 500, reason: "bad <gateway>" }], accessibilitySnapshot: null, domSnippet: "<input value=secret>" },
    environment: { operatingSystem: "Windows", systemRelease: "11", projectName: "chromium", runtimeName: "Node.js", runtimeVersion: process.version, browserName: "chromium", browserVersion: null, viewport: { width: 1280, height: 720 }, locale: "en-US", timezone: "UTC", executionTime: new Date("2026-08-25T12:00:00Z"), commitSha: "deadbeef", branch: "main", ciRunUrl: "https://ci.test/run/1", ciProvider: "CI", safeEnvironment: { CI: "true" } },
    generatedAt: new Date("2026-08-25T12:01:00Z"), automatedWarning: "Automatically generated.", fingerprint: "abcdef1234567890", stability: { classification: "insufficient history", observations: [], sampleSize: 0, failureRate: null, recentTrend: "unknown", consecutivePasses: 0, consecutiveFailures: 0 }, analysis: null, mode,
  };
}

test("failure analysis data and summary omit human review", () => {
  const data = analysis();
  data.analysis = { simpleExplanation: "The test looked for a button, but the button was not there.", likelyCauses: ["The button may have changed."], relatedCodeLocations: [{ rank: 1, filePath: "tests/checkout.spec.ts", lineNumber: 4, confidence: 0.8, suggestedFix: "Update the button locator." }] };
  expect(data).not.toHaveProperty("humanReview");
  const summary = format_failure_summary(data);
  expect(summary).not.toContain("Human review");
  expect(summary).toContain("## Simple explanation");
  expect(summary).toContain("tests/checkout\\.spec\\.ts:4");
  expect(summary).toContain("Update the button locator");
});

test("failure folder name is deterministic", () => {
  expect(make_failure_analysis_folder_name(analysis())).toBe(make_failure_analysis_folder_name(analysis()));
  expect(make_failure_analysis_folder_name(analysis())).toBe("checkout-script-alert-1-script-chromium-abcdef123456-attempt-1");
});

test("saves sanitized JSON, Markdown summary, and copied evidence", async ({}, testInfo) => {
  const data = analysis();
  const screenshot = testInfo.outputPath("failure.png");
  await writeFile(screenshot, "image");
  data.evidence.screenshotPaths = [screenshot];
  const output = await save_failure_analysis(data, testInfo.outputPath("analyses"));
  expect(await readFile(output.markdown, "utf8")).toContain("## Summary");
  expect(await readFile(join(output.directory, "evidence", "failure.png"), "utf8")).toBe("image");
  const persisted = await read_failure_analysis_data(output.data);
  expect(persisted.details.errorMessage).toContain("[REDACTED]");
  expect(persisted.evidence.screenshotPaths).toEqual(["evidence/failure.png"]);
});

test("customer-safe analysis omits internal diagnostics and secrets", () => {
  const data = normalize_failure_analysis_data(analysis("customer-safe"));
  const serialized = JSON.stringify(data);
  expect(serialized).not.toContain("console <secret>");
  expect(serialized).not.toContain("deadbeef");
  expect(serialized).not.toContain("Bearer abcdefghijklmnop");
  expect(serialized).toContain("[REDACTED]");
});

test("normalization trims failure and environment values", () => {
  const data = analysis();
  data.details.testTitle = "  Checkout displays an error  ";
  data.details.testFile = "  tests/checkout.spec.ts  ";
  data.details.errorMessage = "  Expected confirmation message  ";
  data.details.stackTrace = "  Error: confirmation message missing  ";
  data.environment.operatingSystem = "  Windows  ";
  data.environment.projectName = "  chromium  ";
  const normalized = normalize_failure_analysis_data(data);
  expect(normalized.details.testTitle).toBe("Checkout displays an error");
  expect(normalized.details.testFile).toBe("tests/checkout.spec.ts");
  expect(normalized.details.errorMessage).toBe("Expected confirmation message");
  expect(normalized.details.stackTrace).toBe("Error: confirmation message missing");
  expect(normalized.environment.operatingSystem).toBe("Windows");
  expect(normalized.environment.projectName).toBe("chromium");
});

test("normalization removes blank steps and evidence paths", () => {
  const data = analysis();
  data.details.testSteps = ["  Open checkout page  ", "   ", "Submit payment"];
  data.evidence.screenshotPaths = ["  test-results/failure.png  ", ""];
  data.evidence.tracePaths = ["  test-results/trace.zip  ", "   "];
  data.evidence.otherAttachments = ["  test-results/network.txt  ", ""];
  const normalized = normalize_failure_analysis_data(data);
  expect(normalized.details.testSteps).toEqual(["Open checkout page", "Submit payment"]);
  expect(normalized.evidence.screenshotPaths).toEqual(["test-results/failure.png"]);
  expect(normalized.evidence.tracePaths).toEqual(["test-results/trace.zip"]);
  expect(normalized.evidence.otherAttachments).toEqual(["test-results/network.txt"]);
});

test("normalization does not modify its input", () => {
  const data = analysis();
  const original = structuredClone(data);
  normalize_failure_analysis_data(data);
  expect(data).toEqual(original);
});

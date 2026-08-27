import { expect, test } from "@playwright/test";
import { normalize_report_data } from "../src/bug-report-generator";

type ReportData = Parameters<typeof normalize_report_data>[0];

function create_report_data(): ReportData {
  return {
    details: {
      testTitle: "  Checkout displays an error  ",
      testFile: "  tests/checkout.spec.ts  ",
      lineNumber: 24,
      columnNumber: 7,
      status: "failed",
      errorMessage: "  Expected confirmation message  ",
      stackTrace: "  Error: confirmation message missing  ",
      startTime: new Date("2026-08-24T14:00:00.000Z"),
      durationMs: 1250,
      retryNumber: 0,
      testSteps: [
        "  Open checkout page  ",
        "   ",
        "Submit payment",
      ],
      expectedBehavior: null, actualBehavior: null, failedStep: null, tags: [],
    },
    evidence: {
      screenshotPaths: ["  test-results/failure.png  ", ""],
      tracePaths: ["  test-results/trace.zip  ", "   "],
      otherAttachments: ["  test-results/network.txt  ", ""],
      currentUrl: null, consoleMessages: [], pageErrors: [], networkFailures: [], accessibilitySnapshot: null, domSnippet: null,
    },
    environment: {
      operatingSystem: "  Windows  ",
      systemRelease: "  11  ",
      projectName: "  chromium  ",
      browserName: "  chromium  ",
      executionTime: new Date("2026-08-24T14:00:00.000Z"),
      browserVersion: null, viewport: null, locale: null, timezone: null, commitSha: null, branch: null, ciRunUrl: null, ciProvider: null, safeEnvironment: {},
    },
    generatedAt: new Date("2026-08-24T14:01:00.000Z"),
    automatedWarning: "  Requires human review.  ",
    fingerprint: "abcdef1234567890",
    stability: { classification: "insufficient history", observations: [], sampleSize: 0, failureRate: null, recentTrend: "unknown", consecutivePasses: 0, consecutiveFailures: 0 },
    aiAnalysis: null,
    mode: "developer",
  };
}

test.describe("normalize_report_data", () => {
  test("trims report details and environment values", () => {
    const normalized = normalize_report_data(create_report_data());

    expect(normalized.details.testTitle).toBe(
      "Checkout displays an error"
    );
    expect(normalized.details.testFile).toBe(
      "tests/checkout.spec.ts"
    );
    expect(normalized.details.errorMessage).toBe(
      "Expected confirmation message"
    );
    expect(normalized.details.stackTrace).toBe(
      "Error: confirmation message missing"
    );
    expect(normalized.environment.operatingSystem).toBe("Windows");
    expect(normalized.environment.systemRelease).toBe("11");
    expect(normalized.environment.projectName).toBe("chromium");
    expect(normalized.environment.browserName).toBe("chromium");
    expect(normalized.automatedWarning).toBe("Requires human review.");
  });

  test("removes blank test steps and evidence paths", () => {
    const normalized = normalize_report_data(create_report_data());

    expect(normalized.details.testSteps).toEqual([
      "Open checkout page",
      "Submit payment",
    ]);
    expect(normalized.evidence.screenshotPaths).toEqual([
      "test-results/failure.png",
    ]);
    expect(normalized.evidence.tracePaths).toEqual([
      "test-results/trace.zip",
    ]);
    expect(normalized.evidence.otherAttachments).toEqual([
      "test-results/network.txt",
    ]);
  });

  test("does not modify the original report data", () => {
    const report_data = create_report_data();
    const original_report_data = structuredClone(report_data);

    normalize_report_data(report_data);

    expect(report_data).toEqual(original_report_data);
  });
});

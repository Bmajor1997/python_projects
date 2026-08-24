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
    },
    evidence: {
      screenshotPaths: ["  test-results/failure.png  ", ""],
      tracePaths: ["  test-results/trace.zip  ", "   "],
      videoPaths: ["  test-results/video.webm  "],
      otherAttachments: ["  test-results/network.txt  ", ""],
    },
    environment: {
      operatingSystem: "  Windows  ",
      systemRelease: "  11  ",
      projectName: "  chromium  ",
      browserName: "  chromium  ",
      executionTime: new Date("2026-08-24T14:00:00.000Z"),
    },
    humanReview: {
      confirmedDefect: "  Yes  ",
      severity: "  High  ",
      priority: "  P1  ",
      finalTitle: "  Checkout payment fails  ",
      notes: "  Reproduced twice  ",
      ticketUrl: "  https://example.com/BUG-101  ",
    },
    generatedAt: new Date("2026-08-24T14:01:00.000Z"),
    automatedWarning: "  Requires human review.  ",
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
    expect(normalized.evidence.videoPaths).toEqual([
      "test-results/video.webm",
    ]);
    expect(normalized.evidence.otherAttachments).toEqual([
      "test-results/network.txt",
    ]);
  });

  test("converts empty human-review strings to null", () => {
    const report_data = create_report_data();

    report_data.humanReview = {
      confirmedDefect: "   ",
      severity: "",
      priority: "   ",
      finalTitle: "",
      notes: "   ",
      ticketUrl: "",
    };

    const normalized = normalize_report_data(report_data);

    expect(normalized.humanReview).toEqual({
      confirmedDefect: null,
      severity: null,
      priority: null,
      finalTitle: null,
      notes: null,
      ticketUrl: null,
    });
  });

  test("preserves Yes and No confirmed-defect values", () => {
    const yes_report = create_report_data();
    yes_report.humanReview.confirmedDefect = "  Yes  ";

    const no_report = create_report_data();
    no_report.humanReview.confirmedDefect = "  No  ";

    expect(
      normalize_report_data(yes_report).humanReview.confirmedDefect
    ).toBe("Yes");
    expect(
      normalize_report_data(no_report).humanReview.confirmedDefect
    ).toBe("No");
  });

  test("does not modify the original report data", () => {
    const report_data = create_report_data();
    const original_report_data = structuredClone(report_data);

    normalize_report_data(report_data);

    expect(report_data).toEqual(original_report_data);
  });
});
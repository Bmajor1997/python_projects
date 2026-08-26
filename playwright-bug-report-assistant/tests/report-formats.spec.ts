import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { escape_html, format_html } from "../src/html-report";
import { make_report_folder_name } from "../src/file-utils";
import { normalize_report_data } from "../src/bug-report-generator";
import { report_formats_from_env, save_report_bundle, write_pdf } from "../src/report-bundle";
import type { BugReportData } from "../src/types";

function report(mode: BugReportData["mode"] = "developer"): BugReportData {
  return {
    details: { testTitle: "Checkout <script>alert(1)</script>", testFile: "tests/checkout.spec.ts", lineNumber: 4, columnNumber: 2, status: "failed", errorMessage: "Expected <paid> Bearer abcdefghijklmnop", stackTrace: "Error <unsafe>", startTime: new Date("2026-08-25T12:00:00Z"), durationMs: 50, retryNumber: 0, testSteps: ["Submit <payment>"], expectedBehavior: "Receipt <shown>", actualBehavior: "Error <shown>", failedStep: "Submit <payment>", tags: [] },
    evidence: { screenshotPaths: [], tracePaths: [], videoPaths: [], otherAttachments: [], currentUrl: "https://shop.test/?token=secret", consoleMessages: ["console <secret>"], pageErrors: ["page <secret>"], networkFailures: [{ method: "GET", url: "https://api.test/<private>", status: 500, reason: "bad <gateway>" }], accessibilitySnapshot: null, domSnippet: "<input value=secret>" },
    environment: { operatingSystem: "Windows", systemRelease: "11", projectName: "chromium", browserName: "chromium", browserVersion: null, viewport: { width: 1280, height: 720 }, locale: "en-US", timezone: "UTC", executionTime: new Date("2026-08-25T12:00:00Z"), commitSha: "deadbeef", branch: "main", ciRunUrl: "https://ci.test/run/1", ciProvider: "CI", safeEnvironment: { CI: "true" } },
    humanReview: { confirmedDefect: null, severity: null, priority: null, finalTitle: null, notes: null, ticketUrl: null }, generatedAt: new Date("2026-08-25T12:01:00Z"), automatedWarning: "Automatically generated.", fingerprint: "abcdef1234567890", stability: { classification: "insufficient history", observations: [], sampleSize: 0, failureRate: null, recentTrend: "unknown", consecutivePasses: 0, consecutiveFailures: 0 }, aiAnalysis: null, mode,
  };
}

test("HTML escapes all report values", () => {
  expect(escape_html(`<script data-x="1">'&`)).toBe("&lt;script data-x=&quot;1&quot;&gt;&#39;&amp;");
  const html = format_html(report());
  expect(html).not.toContain("<script>alert(1)</script>");
  expect(html).toContain("Checkout &lt;script&gt;alert(1)&lt;/script&gt;");
});

test("customer-safe HTML omits internal diagnostics and secrets", () => {
  const html = format_html(normalize_report_data(report("customer-safe")));
  expect(html).not.toContain("console &lt;secret&gt;");
  expect(html).not.toContain("deadbeef");
  expect(html).not.toContain("Bearer abcdefghijklmnop");
  expect(html).toContain("[REDACTED]");
});

test("report folder name is deterministic", () => {
  expect(make_report_folder_name(report())).toBe(make_report_folder_name(report()));
  expect(make_report_folder_name(report())).toBe("checkout-script-alert-1-script-chromium-abcdef123456");
});

test("each report format can be configured independently", () => {
  expect(report_formats_from_env({ BUG_REPORT_MARKDOWN: "false", BUG_REPORT_HTML: "yes", BUG_REPORT_PDF: "0" })).toEqual({ markdown: false, html: true, pdf: false });
});

test("creates Markdown, HTML, PDF, and copied evidence", async ({}, testInfo) => {
  const data = report(); const screenshot = testInfo.outputPath("failure.png"); await writeFile(screenshot, "image"); data.evidence.screenshotPaths = [screenshot];
  const output = await save_report_bundle(data, testInfo.outputPath("reports"), { markdown: true, html: true, pdf: true }, async (_html, pdf) => writeFile(pdf, "%PDF-test"));
  expect(await readFile(output.markdown!, "utf8")).toContain("## Summary");
  expect(await readFile(output.html!, "utf8")).toContain("evidence/failure.png");
  expect(await readFile(output.pdf!, "utf8")).toBe("%PDF-test");
  expect(await readFile(join(output.directory, "evidence", "failure.png"), "utf8")).toBe("image");
});

test("Chromium renders the professional HTML report to PDF", async ({}, testInfo) => {
  const htmlPath = testInfo.outputPath("bug-report.html"), pdfPath = testInfo.outputPath("bug-report.pdf");
  await writeFile(htmlPath, format_html(normalize_report_data(report())), "utf8");
  await write_pdf(htmlPath, pdfPath);
  expect((await readFile(pdfPath)).subarray(0, 4).toString()).toBe("%PDF");
});

test("PDF failure preserves HTML and Markdown", async ({}, testInfo) => {
  const output = await save_report_bundle(report(), testInfo.outputPath("reports"), { markdown: true, html: true, pdf: true }, async () => { throw new Error("renderer unavailable"); });
  expect(output.pdf).toBeUndefined(); expect(output.pdfError).toBe("renderer unavailable");
  expect(await readFile(output.markdown!, "utf8")).toContain("# Bug:");
  expect(await readFile(output.html!, "utf8")).toContain("<!doctype html>");
});

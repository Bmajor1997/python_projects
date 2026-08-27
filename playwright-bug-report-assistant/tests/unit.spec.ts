import { test, expect } from "@playwright/test";
import { sanitize, sanitize_string, safe_environment } from "../src/sanitizer";
import { normalize_failure_text } from "../src/fingerprint";
import { analyze_stability } from "../src/stability";
import type { HistoryRecord } from "../src/types";
import { create_basic_failure_analysis, run_failure_analysis } from "../src/ai-analysis";
import { expectation_values, friendly_failure_message, friendly_report_title } from "../src/text-utils";

test("recursively redacts secrets and sensitive URL values", () => {
  const value = sanitize({ Authorization: "Bearer top-secret-token", nested: { password: "hunter2", url: "https://example.test/?token=abc&view=ok" } });
  expect(JSON.stringify(value)).not.toContain("hunter2"); expect(JSON.stringify(value)).not.toContain("top-secret-token"); expect(JSON.stringify(value)).not.toContain("token=abc");
});
test("redacts token-shaped text and only exposes allowlisted environment values", () => {
  expect(sanitize_string("Bearer abcdefghijklmnop")).toBe("[REDACTED]");
  expect(safe_environment({ SAFE: "yes", SECRET: "no" }, ["SAFE"])).toEqual({ SAFE: "yes" });
});
test("keeps ordinary error text readable instead of URL-encoding it", () => {
  const error = 'Error: failed\nExpected: "Payment approved"\nReceived: "Payment declined"';
  expect(sanitize_string(error)).toBe(error);
  expect(expectation_values(error)).toEqual({ expected: "Payment approved", received: "Payment declined" });
  expect(friendly_failure_message(error)).toBe('Expected the page to say "Payment approved", but it said "Payment declined".');
  expect(friendly_report_title(error, "technical > name")).toBe('Problem: "Payment declined" appeared instead of "Payment approved"');
});
test("normalizes volatile identifiers and line numbers", () => {
  expect(normalize_failure_text("Failure 12345678901 at C:\\x.ts:42:8")).toBe("failure <number> at c:/x.ts:<line>");
});
test("classifies alternating results as likely flaky with evidence", () => {
  const rows: HistoryRecord[] = ["failed", "passed", "failed"].map((status, i) => ({ fingerprint: "x", testTitle: "t", status, browserName: "chromium", isCI: true, timestamp: new Date(i * 1000).toISOString(), retryNumber: i }));
  const result = analyze_stability(rows); expect(result.classification).toBe("likely flaky"); expect(result.observations.length).toBeGreaterThan(0);
});
test("does not overclaim with too little history", () => {
  expect(analyze_stability([], 3).classification).toBe("insufficient history");
});
test("failure analysis is simple and falls back when a provider fails", async ({}, testInfo) => {
  const testFile = testInfo.outputPath("checkout.spec.ts");
  await import("node:fs/promises").then(({ writeFile }) => writeFile(testFile, "test('checkout', () => {});"));
  const data = { details: { testTitle: "checkout", testFile, lineNumber: 1, errorMessage: "Timeout waiting for the Pay button", expectedBehavior: null, actualBehavior: null, stackTrace: null }, evidence: { networkFailures: [], pageErrors: [], consoleMessages: [] }, environment: {}, stability: { classification: "insufficient history" } } as never;
  const basic = create_basic_failure_analysis(data, testInfo.outputDir);
  expect(basic.simpleExplanation).toContain("took too long");
  expect(basic.likelyCauses).toHaveLength(1);
  expect(basic.relatedCodeLocations).toEqual([{ rank: 1, filePath: "checkout.spec.ts", lineNumber: 1, confidence: 0.8, suggestedFix: expect.any(String) }]);
  expect(await run_failure_analysis(data, async () => { throw new Error("offline"); }, { projectRoot: testInfo.outputDir })).toEqual(basic);
});

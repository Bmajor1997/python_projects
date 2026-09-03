import { test, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { sanitize, sanitize_string, safe_environment } from "../src/sanitizer";
import { normalize_failure_text } from "../src/fingerprint";
import { analyze_stability } from "../src/stability";
import type { HistoryRecord } from "../src/types";
import { create_basic_failure_analysis, run_failure_analysis } from "../src/ai-analysis";
import { append_history, read_history } from "../src/history";
import { OpenAIAnalysisProvider } from "../src/providers";
import { expectation_values, friendly_failure_message, friendly_report_title } from "../src/text-utils";

test("recursively redacts secrets and sensitive URL values", () => {
  const value = sanitize({ Authorization: "Bearer top-secret-token", nested: { password: "hunter2", url: "https://example.test/?token=abc&view=ok" } });
  expect(JSON.stringify(value)).not.toContain("hunter2"); expect(JSON.stringify(value)).not.toContain("top-secret-token"); expect(JSON.stringify(value)).not.toContain("token=abc");
});
test("redacts token-shaped text and only exposes allowlisted environment values", () => {
  expect(sanitize_string("Bearer abcdefghijklmnop")).toBe("[REDACTED]");
  expect(safe_environment({ SAFE: "yes", SECRET: "no" }, ["SAFE"])).toEqual({ SAFE: "yes" });
});
test("redacts email addresses from provider-bound text", () => {
  expect(sanitize_string("Customer jane@example.com failed checkout")).toBe("Customer [REDACTED] failed checkout");
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
  await writeFile(testFile, "test('checkout', () => {});");
  const data = { details: { testTitle: "checkout", testFile, lineNumber: 1, errorMessage: "Timeout waiting for the Pay button", expectedBehavior: null, actualBehavior: null, stackTrace: null }, evidence: { networkFailures: [], pageErrors: [], consoleMessages: [] }, environment: {}, stability: { classification: "insufficient history" } } as never;
  const basic = create_basic_failure_analysis(data, testInfo.outputDir);
  expect(basic.simpleExplanation).toContain("took too long");
  expect(basic.likelyCauses).toHaveLength(3);
  expect(basic.relatedCodeLocations).toEqual([{ rank: 1, filePath: "checkout.spec.ts", lineNumber: 1, confidence: 0.7, suggestedFix: expect.stringContaining("time limit") }]);
  expect(await run_failure_analysis(data, async () => { throw new Error("offline"); }, { projectRoot: testInfo.outputDir })).toEqual(basic);
});

test("failure analysis prefers application stack locations and ignores generated dependencies", async ({}, testInfo) => {
  const sourceDirectory = join(testInfo.outputDir, "src"), dependencyDirectory = join(testInfo.outputDir, "node_modules", "library");
  await mkdir(sourceDirectory, { recursive: true });
  await mkdir(dependencyDirectory, { recursive: true });
  await writeFile(join(sourceDirectory, "checkout.ts"), "one\ntwo\nthree");
  await writeFile(join(dependencyDirectory, "index.js"), "one\ntwo\nthree");
  const testFile = join(testInfo.outputDir, "checkout.spec.ts");
  await writeFile(testFile, "one\ntwo\nthree");
  const data = { details: { testTitle: "checkout", testFile, lineNumber: 2, errorMessage: "Expected: paid\nReceived: declined", expectedBehavior: "paid", actualBehavior: "declined", stackTrace: `at checkout (${join(sourceDirectory, "checkout.ts")}:2:1)\nat library (${join(dependencyDirectory, "index.js")}:2:1)` }, evidence: { networkFailures: [], pageErrors: [], consoleMessages: [] }, environment: {}, stability: { classification: "insufficient history" } } as never;
  const result = create_basic_failure_analysis(data, testInfo.outputDir);
  expect(result.simpleExplanation).toBe("The test wanted to see paid, but it saw declined instead.");
  expect(result.relatedCodeLocations[0]).toMatchObject({ rank: 1, filePath: "src/checkout.ts", lineNumber: 2, confidence: 0.9 });
  expect(result.relatedCodeLocations.some(location => location.filePath.includes("node_modules"))).toBe(false);
});
test("serializes concurrent history writes", async ({}, testInfo) => {
  const path = testInfo.outputPath("history.json");
  await Promise.all(Array.from({ length: 20 }, (_, index) => append_history(path, { fingerprint: `f${index}`, testTitle: "test", status: "failed", browserName: "chromium", isCI: false, timestamp: new Date(index * 1000).toISOString(), retryNumber: 0 })));
  expect(await read_history(path)).toHaveLength(20);
});
test("OpenAI provider requests structured output without a live API call", async () => {
  let request: unknown;
  const client = { responses: { create: async (value: unknown) => { request = value; return { output_text: JSON.stringify({ simpleExplanation: "The checkout timed out.", likelyCauses: ["The button never appeared."], relatedCodeLocations: [] }) }; } } };
  const result = await new OpenAIAnalysisProvider(client as never).analyze({ candidateCodeLocations: [] }, { model: "test-model", timeoutMs: 1000 });
  expect(result.provider).toBe("openai");
  expect(result.analysis).toMatchObject({ simpleExplanation: "The checkout timed out." });
  expect(request).toMatchObject({ model: "test-model", store: false, text: { format: { type: "json_schema", strict: true } } });
});

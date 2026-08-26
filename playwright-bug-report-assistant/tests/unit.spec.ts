import { test, expect } from "@playwright/test";
import { sanitize, sanitize_string, safe_environment } from "../src/sanitizer";
import { normalize_failure_text } from "../src/fingerprint";
import { analyze_stability } from "../src/stability";
import type { HistoryRecord } from "../src/types";
import { run_ai_analysis } from "../src/ai-analysis";
import { GitHubIssuePublisher } from "../src/publisher";

test("recursively redacts secrets and sensitive URL values", () => {
  const value = sanitize({ Authorization: "Bearer top-secret-token", nested: { password: "hunter2", url: "https://example.test/?token=abc&view=ok" } });
  expect(JSON.stringify(value)).not.toContain("hunter2"); expect(JSON.stringify(value)).not.toContain("top-secret-token"); expect(JSON.stringify(value)).not.toContain("token=abc");
});
test("redacts token-shaped text and only exposes allowlisted environment values", () => {
  expect(sanitize_string("Bearer abcdefghijklmnop")).toBe("[REDACTED]");
  expect(safe_environment({ SAFE: "yes", SECRET: "no" }, ["SAFE"])).toEqual({ SAFE: "yes" });
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
test("AI analysis is optional and falls back on provider failure", async () => {
  const data = { details: { errorMessage: "secret" }, evidence: {}, environment: {}, stability: {} } as never;
  expect(await run_ai_analysis(data, undefined, { enabled: false })).toBeNull();
  expect(await run_ai_analysis(data, async () => { throw new Error("offline"); }, { enabled: true })).toBeNull();
});
test("publishing dry-run performs no external request", async () => {
  const publisher = new GitHubIssuePublisher("owner", "repo", "secret-token");
  expect(await publisher.publish({ title: "Bug", body: "Preview", fingerprint: "abc" }, true)).toBeNull();
});

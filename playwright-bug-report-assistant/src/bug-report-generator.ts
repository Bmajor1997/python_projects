import { existsSync } from "node:fs";
import { platform, release } from "node:os";
import type { TestCase, TestResult } from "@playwright/test/reporter";
import { clean_error_text, expectation_values, friendly_failure_message } from "./text-utils";
import { sanitize, safe_environment } from "./sanitizer";
import { create_fingerprint } from "./fingerprint";
import { analyze_stability } from "./stability";
import type { EnvironmentDetails, EvidenceFiles, FailureAnalysisData, FailureDetails, HistoryRecord, ReportMode } from "./types";

type FailedTest = { test: TestCase; result: TestResult };

export function get_test_steps(result: TestResult): string[] {
  const titles: string[] = [], pending = [...result.steps];
  while (pending.length) { const step = pending.shift(); if (!step) continue; if (step.category === "test.step") titles.push(step.title); pending.unshift(...step.steps); }
  return titles;
}
export function collect_failure_details({ test, result }: FailedTest): FailureDetails {
  const primary = result.errors[0];
  const steps = get_test_steps(result);
  const rawError = clean_error_text(primary?.message ?? "The test failed without an error message.");
  const comparison = expectation_values(rawError);
  return { testTitle: test.titlePath().join(" > "), testFile: test.location.file, lineNumber: test.location.line, columnNumber: test.location.column,
    status: result.status, errorMessage: friendly_failure_message(rawError), stackTrace: primary?.stack ? clean_error_text(primary.stack) : null,
    startTime: result.startTime, durationMs: result.duration, retryNumber: result.retry, testSteps: steps, expectedBehavior: comparison?.expected ?? null, actualBehavior: comparison?.received ?? null,
    failedStep: steps.at(-1) ?? null, tags: test.tags ?? [] };
}
function parse_json_attachment(result: TestResult, name: string): unknown | null {
  const attachment = result.attachments.find(a => a.name === name && a.body);
  if (!attachment?.body) return null;
  try { return JSON.parse(attachment.body.toString("utf8")); } catch { return null; }
}
export function find_evidence(result: TestResult): EvidenceFiles {
  const evidence: EvidenceFiles = { screenshotPaths: [], tracePaths: [], otherAttachments: [], currentUrl: null, consoleMessages: [], pageErrors: [], networkFailures: [], accessibilitySnapshot: null, domSnippet: null };
  for (const attachment of result.attachments) {
    if (!attachment.path || !existsSync(attachment.path)) continue;
    const name = attachment.name.toLowerCase(), type = attachment.contentType.toLowerCase();
    if (type.startsWith("image/") || name.includes("screenshot")) evidence.screenshotPaths.push(attachment.path);
    else if (name.includes("trace")) evidence.tracePaths.push(attachment.path);
    else if (type.startsWith("video/") || name.includes("video")) continue;
    else evidence.otherAttachments.push(attachment.path);
  }
  const context = parse_json_attachment(result, "bug-report-context") as Partial<EvidenceFiles> | null;
  return sanitize({ ...evidence, ...(context ?? {}), screenshotPaths: evidence.screenshotPaths, tracePaths: evidence.tracePaths, otherAttachments: evidence.otherAttachments });
}
export function collect_environment({ test, result }: FailedTest): EnvironmentDetails {
  const project = test.parent.project();
  const os = platform() === "win32" ? "Windows" : platform() === "darwin" ? "macOS" : platform() === "linux" ? "Linux" : platform();
  const server = process.env.GITHUB_SERVER_URL, repo = process.env.GITHUB_REPOSITORY, run = process.env.GITHUB_RUN_ID;
  const allowlist = (process.env.BUG_REPORT_SAFE_ENV ?? "CI,NODE_ENV").split(",").map(x => x.trim()).filter(Boolean);
  return { operatingSystem: os, systemRelease: release(), projectName: project?.name ?? "Unknown", runtimeName: "Node.js", runtimeVersion: process.version, browserName: project?.use.browserName ?? null, browserVersion: null,
    viewport: project?.use.viewport ?? null, locale: project?.use.locale ?? null, timezone: project?.use.timezoneId ?? null, executionTime: result.startTime,
    commitSha: process.env.GITHUB_SHA ?? process.env.CI_COMMIT_SHA ?? null, branch: process.env.GITHUB_REF_NAME ?? process.env.CI_COMMIT_REF_NAME ?? null,
    ciRunUrl: server && repo && run ? `${server}/${repo}/actions/runs/${run}` : null, ciProvider: process.env.GITHUB_ACTIONS ? "GitHub Actions" : process.env.CI ? "CI" : null,
    safeEnvironment: safe_environment(process.env, allowlist) };
}
export function build_failure_analysis_data(details: FailureDetails, evidence: EvidenceFiles, environment: EnvironmentDetails, mode: ReportMode = "developer", history: HistoryRecord[] = []): FailureAnalysisData {
  const fingerprint = create_fingerprint(details, environment.browserName ?? environment.runtimeName, evidence.currentUrl);
  return { details, evidence, environment, generatedAt: new Date(), automatedWarning: "Automatically generated failure analysis. AI suggestions and inferred fields require verification.",
    fingerprint, stability: analyze_stability(history.filter(x => x.testTitle === details.testTitle && (!x.fingerprint || x.fingerprint === fingerprint))), analysis: null, mode,
    schemaVersion: "1.0", toolVersion: "1.0.0", warnings: [] };
}

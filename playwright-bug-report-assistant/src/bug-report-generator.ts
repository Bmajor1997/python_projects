import { existsSync } from "node:fs";
import { platform, release } from "node:os";
import { join, relative } from "node:path";
import type { TestResult } from "@playwright/test/reporter";
import { make_filename, save_file } from "./file-utils";
import { clean_error_text, escape_markdown } from "./text-utils";
import { sanitize, safe_environment } from "./sanitizer";
import { categorize_failure, create_fingerprint } from "./fingerprint";
import { analyze_stability } from "./stability";
import type { BugReportData, EnvironmentDetails, EvidenceFiles, FailedTest, FailureDetails, HistoryRecord, HumanReview, ReportMode } from "./types";

export function get_test_steps(result: TestResult): string[] {
  const titles: string[] = [], pending = [...result.steps];
  while (pending.length) { const step = pending.shift(); if (!step) continue; if (step.category === "test.step") titles.push(step.title); pending.unshift(...step.steps); }
  return titles;
}
export function collect_failure_details({ test, result }: FailedTest): FailureDetails {
  const primary = result.errors[0];
  const steps = get_test_steps(result);
  return { testTitle: test.titlePath().join(" > "), testFile: test.location.file, lineNumber: test.location.line, columnNumber: test.location.column,
    status: result.status, errorMessage: clean_error_text(primary?.message ?? "The test failed without an error message."), stackTrace: primary?.stack ? clean_error_text(primary.stack) : null,
    startTime: result.startTime, durationMs: result.duration, retryNumber: result.retry, testSteps: steps, expectedBehavior: null, actualBehavior: primary?.message ? clean_error_text(primary.message) : null,
    failedStep: steps.at(-1) ?? null, tags: test.tags ?? [] };
}
function parse_json_attachment(result: TestResult, name: string): unknown | null {
  const attachment = result.attachments.find(a => a.name === name && a.body);
  if (!attachment?.body) return null;
  try { return JSON.parse(attachment.body.toString("utf8")); } catch { return null; }
}
export function find_evidence(result: TestResult): EvidenceFiles {
  const evidence: EvidenceFiles = { screenshotPaths: [], tracePaths: [], videoPaths: [], otherAttachments: [], currentUrl: null, consoleMessages: [], pageErrors: [], networkFailures: [], accessibilitySnapshot: null, domSnippet: null };
  for (const attachment of result.attachments) {
    if (!attachment.path || !existsSync(attachment.path)) continue;
    const name = attachment.name.toLowerCase(), type = attachment.contentType.toLowerCase();
    if (type.startsWith("image/") || name.includes("screenshot")) evidence.screenshotPaths.push(attachment.path);
    else if (name.includes("trace")) evidence.tracePaths.push(attachment.path);
    else if (type.startsWith("video/") || name.includes("video")) evidence.videoPaths.push(attachment.path);
    else evidence.otherAttachments.push(attachment.path);
  }
  const context = parse_json_attachment(result, "bug-report-context") as Partial<EvidenceFiles> | null;
  return sanitize({ ...evidence, ...(context ?? {}), screenshotPaths: evidence.screenshotPaths, tracePaths: evidence.tracePaths, videoPaths: evidence.videoPaths, otherAttachments: evidence.otherAttachments });
}
export function collect_environment({ test, result }: FailedTest): EnvironmentDetails {
  const project = test.parent.project();
  const os = platform() === "win32" ? "Windows" : platform() === "darwin" ? "macOS" : platform() === "linux" ? "Linux" : platform();
  const server = process.env.GITHUB_SERVER_URL, repo = process.env.GITHUB_REPOSITORY, run = process.env.GITHUB_RUN_ID;
  const allowlist = (process.env.BUG_REPORT_SAFE_ENV ?? "CI,NODE_ENV").split(",").map(x => x.trim()).filter(Boolean);
  return { operatingSystem: os, systemRelease: release(), projectName: project?.name ?? "Unknown", browserName: project?.use.browserName ?? "Unknown", browserVersion: null,
    viewport: project?.use.viewport ?? null, locale: project?.use.locale ?? null, timezone: project?.use.timezoneId ?? null, executionTime: result.startTime,
    commitSha: process.env.GITHUB_SHA ?? process.env.CI_COMMIT_SHA ?? null, branch: process.env.GITHUB_REF_NAME ?? process.env.CI_COMMIT_REF_NAME ?? null,
    ciRunUrl: server && repo && run ? `${server}/${repo}/actions/runs/${run}` : null, ciProvider: process.env.GITHUB_ACTIONS ? "GitHub Actions" : process.env.CI ? "CI" : null,
    safeEnvironment: safe_environment(process.env, allowlist) };
}
const empty_review = (): HumanReview => ({ confirmedDefect: null, severity: null, priority: null, finalTitle: null, notes: null, ticketUrl: null });
export function build_report_data(details: FailureDetails, evidence: EvidenceFiles, environment: EnvironmentDetails, mode: ReportMode = "developer", history: HistoryRecord[] = []): BugReportData {
  const fingerprint = create_fingerprint(details, environment.browserName, evidence.currentUrl);
  return { details, evidence, environment, humanReview: empty_review(), generatedAt: new Date(), automatedWarning: "Automatically generated. AI suggestions and inferred fields require human review.",
    fingerprint, stability: analyze_stability(history.filter(x => x.testTitle === details.testTitle)), aiAnalysis: null, mode };
}
export function normalize_report_data(data: BugReportData): BugReportData {
  const trim = (value: unknown): unknown => {
    if (typeof value === "string") { const text = value.trim(); return text || null; }
    if (value instanceof Date) return new Date(value.getTime());
    if (Array.isArray(value)) return value.map(trim).filter(item => item !== null);
    if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, trim(item)]));
    return value;
  };
  const clean = sanitize(trim(structuredClone(data))) as BugReportData;
  if (clean.mode === "customer-safe") {
    clean.details.testFile = "[INTERNAL PATH OMITTED]";
    clean.details.stackTrace = null;
    clean.evidence.consoleMessages = [];
    clean.evidence.pageErrors = [];
    clean.evidence.networkFailures = [];
    clean.evidence.domSnippet = null;
    clean.evidence.accessibilitySnapshot = null;
    clean.environment.safeEnvironment = {};
    clean.environment.commitSha = null;
    clean.environment.branch = null;
  }
  return clean;
}
const show = (value: unknown) => value === null || value === undefined || value === "" ? "Unavailable" : String(value);
const links = (paths: string[]) => paths.length ? paths.map(p => `- [${escape_markdown(relative(process.cwd(), p) || p)}](${p.replace(/\\/g, "/")})`).join("\n") : "- None captured";
export function format_markdown(input: BugReportData): string {
  const data = normalize_report_data(input), { details: d, evidence: e, environment: n } = data;
  const lines = [`# ${escape_markdown(data.aiAnalysis?.title ?? `Bug: ${d.testTitle}`)}`, "", `> ${data.automatedWarning}`, "", "## Summary", "",
    `- **Status:** ${d.status}`, `- **Category:** ${categorize_failure(d.errorMessage)}`, `- **Fingerprint:** \`${data.fingerprint}\``, `- **Stability:** ${data.stability.classification} (${data.stability.sampleSize} samples)`,
    `- **Error:** ${escape_markdown(d.errorMessage)}`, "", "## Reproduction", "", `- **Test:** ${escape_markdown(d.testTitle)}`, `- **Failed step:** ${show(d.failedStep)}`,
    `- **Expected:** ${show(d.expectedBehavior)}`, `- **Actual:** ${show(d.actualBehavior)}`, `- **URL:** ${show(e.currentUrl)}`, `- **Retry:** ${d.retryNumber}`,
    "", "### Steps", "", ...(d.testSteps.length ? d.testSteps.map((s, i) => `${i + 1}. ${escape_markdown(s)}`) : ["Unavailable"]), "", "## Environment", "",
    `- **Browser/project:** ${n.browserName} / ${n.projectName}`, `- **Viewport:** ${n.viewport ? `${n.viewport.width}×${n.viewport.height}` : "Unavailable"}`, `- **OS:** ${n.operatingSystem} ${n.systemRelease}`,
    `- **Locale/timezone:** ${show(n.locale)} / ${show(n.timezone)}`, `- **Commit/branch:** ${show(n.commitSha)} / ${show(n.branch)}`, `- **CI run:** ${show(n.ciRunUrl)}`, "", "## Evidence", "",
    "### Screenshots", links(e.screenshotPaths), "", "### Traces", links(e.tracePaths), "", "### Videos", links(e.videoPaths), "", "### Other attachments", links(e.otherAttachments)];
  if (data.mode === "developer") lines.push("", "### Diagnostics", "", `**Console:** ${e.consoleMessages.length ? e.consoleMessages.map(escape_markdown).join("; ") : "None captured"}`, "", `**Page errors:** ${e.pageErrors.length ? e.pageErrors.map(escape_markdown).join("; ") : "None captured"}`, "", `**Network failures:** ${e.networkFailures.length ? e.networkFailures.map(x => `${x.method} ${x.status ?? "failed"} ${x.url}`).join("; ") : "None captured"}`, "", "### Stack trace", "", "```text", d.stackTrace ?? "Unavailable", "```");
  if (data.aiAnalysis) lines.push("", "## AI suggestions — human review required", "", data.aiAnalysis.summary, "", `- **Likely cause:** ${data.aiAnalysis.likelyCause}`, `- **Confidence:** ${Math.round(data.aiAnalysis.confidence * 100)}%`, "- **Assumptions:**", ...data.aiAnalysis.assumptions.map(x => `  - ${x}`));
  lines.push("", "## Stability evidence", "", ...(data.stability.observations.length ? data.stability.observations.map(x => `- ${x}`) : ["- Insufficient observations for a specific finding."]), "", "## Human review", "", "- Confirmed defect: Pending", "- Severity: Pending", "- Priority: Pending", "- Final title: Pending", "- Ticket URL: Pending");
  return lines.join("\n");
}
export function format_json(data: BugReportData): string { return JSON.stringify(normalize_report_data(data), null, 2); }
export function format_plain_text(data: BugReportData): string { return format_markdown(data).replace(/^#+\s*/gm, "").replace(/[*`]/g, ""); }
export function generate_bug_report(data: BugReportData, format: "markdown" | "json" | "plain_text"): string {
  if (format === "markdown") return format_markdown(data); if (format === "json") return format_json(data); if (format === "plain_text") return format_plain_text(data); throw new Error(`Unsupported report format: ${format}`);
}
export async function save_bug_report(failure: FailedTest, outputDirectory: string, format: "markdown" | "json" | "plain_text", mode: ReportMode = "developer", history: HistoryRecord[] = []): Promise<string> {
  const details = collect_failure_details(failure), evidence = find_evidence(failure.result), environment = collect_environment(failure);
  const data = build_report_data(details, evidence, environment, mode, history), contents = generate_bug_report(data, format), extension = format === "markdown" ? ".md" : format === "json" ? ".json" : ".txt";
  const path = join(outputDirectory, make_filename(data).replace(/\.md$/, extension)); await save_file(path, contents); return path;
}

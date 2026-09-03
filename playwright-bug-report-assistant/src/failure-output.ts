import { relative } from "node:path";
import { categorize_failure } from "./fingerprint";
import { sanitize } from "./sanitizer";
import { escape_markdown, friendly_report_title, friendly_test_name } from "./text-utils";
import type { FailureAnalysisData } from "./types";

export function normalize_failure_analysis_data(data: FailureAnalysisData): FailureAnalysisData {
  const trim = (value: unknown): unknown => {
    if (typeof value === "string") { const text = value.trim(); return text || null; }
    if (value instanceof Date) return new Date(value.getTime());
    if (Array.isArray(value)) return value.map(trim).filter(item => item !== null);
    if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, trim(item)]));
    return value;
  };
  const clean = sanitize(trim(structuredClone(data))) as FailureAnalysisData;
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
    clean.context = {};
    clean.evidence.screenshotPaths = [];
    clean.evidence.tracePaths = [];
    clean.evidence.otherAttachments = [];
  }
  return clean;
}

const show = (value: unknown) => value === null || value === undefined || value === "" ? "Unavailable" : String(value);
const links = (paths: string[]) => paths.length ? paths.map(p => `- [${escape_markdown(relative(process.cwd(), p) || p)}](${p.replace(/\\/g, "/")})`).join("\n") : "- None captured";

export function format_failure_summary(input: FailureAnalysisData): string {
  const data = normalize_failure_analysis_data(input), { details: d, evidence: e, environment: n } = data;
  const lines = [`# ${escape_markdown(friendly_report_title(d.errorMessage, d.testTitle, d.expectedBehavior, d.actualBehavior))}`, "", `> ${data.automatedWarning}`, "", "## Summary", "",
    `- **Schema/tool version:** ${data.schemaVersion ?? "legacy"} / ${data.toolVersion ?? "unknown"}`,
    `- **Analysis provider:** ${data.analysisMetadata?.provider ?? "deterministic"}${data.analysisMetadata?.model ? ` (${data.analysisMetadata.model})` : ""}${data.analysisMetadata?.fallbackUsed ? " — deterministic fallback used" : ""}`,
    `- **Status:** ${d.status}`, `- **Category:** ${categorize_failure(d.errorMessage)}`, `- **Fingerprint:** \`${data.fingerprint}\``, `- **Stability:** ${data.stability.classification} (${data.stability.sampleSize} samples)`,
    `- **What went wrong:** ${escape_markdown(d.errorMessage)}`, "", "## Details", "", `- **Task:** ${escape_markdown(friendly_test_name(d.testTitle))}`, `- **Failed step:** ${show(d.failedStep)}`,
    `- **Expected:** ${show(d.expectedBehavior)}`, `- **Actual:** ${show(d.actualBehavior)}`, `- **URL:** ${show(e.currentUrl)}`, `- **Retry:** ${d.retryNumber}`,
    "", "### Steps", "", ...(d.testSteps.length ? d.testSteps.map((s, i) => `${i + 1}. ${escape_markdown(s)}`) : ["Unavailable"]), "", "## Environment", "",
    `- **Runtime/project:** ${n.runtimeName}${n.runtimeVersion ? ` ${n.runtimeVersion}` : ""} / ${n.projectName}`, `- **Browser:** ${show(n.browserName)}`, `- **Viewport:** ${n.viewport ? `${n.viewport.width}×${n.viewport.height}` : "Unavailable"}`, `- **OS:** ${n.operatingSystem} ${n.systemRelease}`,
    `- **Locale/timezone:** ${show(n.locale)} / ${show(n.timezone)}`, `- **Commit/branch:** ${show(n.commitSha)} / ${show(n.branch)}`, `- **CI run:** ${show(n.ciRunUrl)}`, "", "## Evidence", "",
    "### Screenshots", links(e.screenshotPaths), "", "### Traces", links(e.tracePaths), "", "### Other attachments", links(e.otherAttachments)];
  if (data.mode === "developer") lines.push("", "### Diagnostics", "", `**Console:** ${e.consoleMessages.length ? e.consoleMessages.map(escape_markdown).join("; ") : "None captured"}`, "", `**Page errors:** ${e.pageErrors.length ? e.pageErrors.map(escape_markdown).join("; ") : "None captured"}`, "", `**Network failures:** ${e.networkFailures.length ? e.networkFailures.map(x => `${x.method} ${x.status ?? "failed"} ${x.url}`).join("; ") : "None captured"}`, "", "### Stack trace", "", "```text", d.stackTrace ?? "Unavailable", "```");
  if (data.analysis) {
    lines.push("", "## Simple explanation", "", escape_markdown(data.analysis.simpleExplanation), "", "## Most likely causes", "", ...data.analysis.likelyCauses.map((cause, index) => `${index + 1}. ${escape_markdown(cause)}`), "", "## Related code locations", "");
    lines.push(...(data.analysis.relatedCodeLocations.length ? data.analysis.relatedCodeLocations.map(location => `${location.rank}. **${escape_markdown(location.filePath)}:${location.lineNumber}** — ${Math.round(location.confidence * 100)}% confidence\n   - Suggested fix: ${escape_markdown(location.suggestedFix)}`) : ["No trustworthy code location was found."]));
  }
  if (data.warnings?.length) lines.push("", "## Warnings", "", ...data.warnings.map(warning => `- **${escape_markdown(warning.code)}:** ${escape_markdown(warning.message)}`));
  lines.push("", "## Stability evidence", "", ...(data.stability.observations.length ? data.stability.observations.map(x => `- ${x}`) : ["- Insufficient observations for a specific finding."]));
  return lines.join("\n");
}

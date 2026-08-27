import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { categorize_failure } from "./fingerprint";
import { sanitize } from "./sanitizer";
import { friendly_test_name } from "./text-utils";
import type { FailureAnalysis, FailureAnalysisData, RelatedCodeLocation } from "./types";

export type AIAnalyzer = (sanitizedInput: unknown, options: { model: string; timeoutMs: number }) => Promise<unknown>;

function simple_explanation(data: FailureAnalysisData): string {
  const { details } = data;
  const plainValue = (value: string | null): string | null => value && value.length <= 80 && !/[<>{}\[\]\\/]/.test(value) ? value.replace(/[`"']/g, "").trim() : null;
  const expected = plainValue(details.expectedBehavior), actual = plainValue(details.actualBehavior);
  if (expected && actual) return `The test wanted to see ${expected}, but it saw ${actual} instead.`;
  const name = friendly_test_name(details.testTitle);
  const category = categorize_failure(details.errorMessage);
  if (category === "timeout") return `The ${name} task waited for something to happen, but it took too long.`;
  if (category === "selector") return `The ${name} task looked for something, but it could not find it.`;
  if (category === "network" || category === "api") return `The ${name} task needed information from another service, but that request did not work.`;
  if (category === "authentication") return `The ${name} task could not prove that the user was signed in.`;
  return `The ${name} task tried to finish its job, but something went wrong.`;
}

function likely_causes(data: FailureAnalysisData): string[] {
  const causes: string[] = [];
  const category = categorize_failure(data.details.errorMessage);
  const categoryCauses: Record<typeof category, [string, string, string]> = {
    selector: ["The thing the task looked for may have changed its name.", "The program may not have finished creating the missing item.", "The task may be looking in the wrong place."],
    timeout: ["The program or action may be taking too long.", "The task may be waiting for something that never happens.", "A slow service may be stopping the task from finishing."],
    authentication: ["The user may not have been signed in.", "The sign-in information may be missing or expired.", "The test may have been sent back to the sign-in page."],
    api: ["A service used by the program may have returned the wrong answer.", "The program may have sent the wrong information to the service.", "The service may have been unavailable when the task ran."],
    network: ["The program may have lost its connection.", "A service used by the program may not have answered.", "The request may have gone to the wrong place."],
    visual: ["The page may look different from the saved picture.", "The browser size or display settings may be different.", "The page may not have finished drawing before the picture was taken."],
    assertion: ["The program may have returned the wrong value.", "The check may still expect an old value.", "The program may not have finished updating before it was checked."],
    environment: ["The test machine may be set up differently.", "A needed setting or file may be missing.", "The browser version may behave differently."],
    unknown: ["The program may not have reached the expected step.", "The input data may be missing or different.", "An earlier action may not have finished correctly."],
  };
  causes.push(categoryCauses[category][0]);
  const network = data.evidence.networkFailures[0];
  if (network) causes.push("A request needed by the page did not work.");
  if (data.evidence.pageErrors[0]) causes.push("The page itself reported that something broke.");
  else if (data.evidence.consoleMessages[0]) causes.push("The browser reported a problem while the page was running.");
  else if (data.stability.classification === "likely flaky") causes.push("The test history changes between passing and failing, so timing or unstable data may be involved.");
  causes.push(...categoryCauses[category].slice(1));
  return [...new Set(causes)].slice(0, 3);
}

function valid_repository_location(path: string, lineNumber: number, projectRoot: string): { filePath: string; lineNumber: number } | null {
  const absolute = resolve(projectRoot, path);
  const repositoryPath = relative(projectRoot, absolute);
  if (repositoryPath.startsWith("..") || isAbsolute(repositoryPath) || !existsSync(absolute)) return null;
  const segments = repositoryPath.replace(/\\/g, "/").split("/");
  if (segments.some(segment => ["node_modules", "test-results", "playwright-report", "blob-report", "dist", "release", ".git"].includes(segment))) return null;
  const lineCount = readFileSync(absolute, "utf8").split(/\r?\n/).length;
  if (!Number.isInteger(lineNumber) || lineNumber < 1 || lineNumber > lineCount) return null;
  return { filePath: repositoryPath.replace(/\\/g, "/"), lineNumber };
}

function related_code_locations(data: FailureAnalysisData, projectRoot: string): RelatedCodeLocation[] {
  const candidates: Array<{ path: string; line: number; source: "test" | "stack" }> = [];
  if (data.details.testFile && data.details.lineNumber) candidates.push({ path: data.details.testFile, line: data.details.lineNumber, source: "test" });
  const stack = data.details.stackTrace ?? "";
  const extensions = "ts|tsx|js|jsx|mjs|cjs|py|java|cs|go|rb|php|rs|cpp|cc|c|h|hpp";
  for (const match of stack.matchAll(new RegExp(`(?:\\(|\\bat\\s+|^\\s*)([^()\\r\\n\"]+?\\.(?:${extensions})):(\\d+)(?::\\d+)?`, "gmi"))) candidates.push({ path: match[1].trim(), line: Number(match[2]), source: "stack" });
  for (const match of stack.matchAll(/File\s+"([^"]+\.py)",\s+line\s+(\d+)/gi)) candidates.push({ path: match[1], line: Number(match[2]), source: "stack" });
  for (const match of stack.matchAll(/\bin\s+([^\r\n]+?\.cs):line\s+(\d+)/gi)) candidates.push({ path: match[1].trim(), line: Number(match[2]), source: "stack" });
  const category = categorize_failure(data.details.errorMessage);
  const suggestedFix = (filePath: string): string => {
    const isTest = /(^|\/)(tests?|specs?)(\/|$)|\.spec\.[jt]sx?$/.test(filePath);
    if (category === "selector") return isTest ? "Update the locator so the test looks for the element that is really on the page." : "Make sure this code shows the expected page element before the test looks for it.";
    if (category === "timeout") return "Check what this line is waiting for and make sure the action can finish before the time limit.";
    if (category === "network" || category === "api") return "Check how this line handles the failed request and make sure the page can recover or show the correct result.";
    if (category === "assertion") return isTest ? "Check that this expected value still matches the correct application behavior." : "Check why this line produces a value different from what the test expects.";
    return isTest ? "Check this test step against the current application behavior and correct the expectation or setup." : "Check the application behavior at this line and correct the state that caused the failure.";
  };
  const resolved = candidates.map(candidate => ({ candidate, location: valid_repository_location(candidate.path, candidate.line, projectRoot) })).filter((item): item is { candidate: typeof candidates[number]; location: { filePath: string; lineNumber: number } } => Boolean(item.location));
  resolved.sort((a, b) => {
    const score = (item: typeof a) => item.candidate.source === "stack" && !/(^|\/)(tests?|specs?)(\/|$)|\.spec\.[jt]sx?$/.test(item.location.filePath) ? 3 : item.candidate.source === "stack" ? 2 : 1;
    return score(b) - score(a);
  });
  const unique = new Set<string>();
  const locations: RelatedCodeLocation[] = [];
  for (const { candidate, location } of resolved) {
    const key = `${location.filePath}:${location.lineNumber}`;
    if (unique.has(key)) continue;
    unique.add(key);
    const rank = (locations.length + 1) as 1 | 2 | 3;
    const applicationStack = candidate.source === "stack" && !/(^|\/)(tests?|specs?)(\/|$)|\.spec\.[jt]sx?$/.test(location.filePath);
    const confidence = applicationStack ? 0.9 : candidate.source === "stack" ? 0.8 : 0.7;
    locations.push({ rank, ...location, confidence: Math.max(0.5, confidence - locations.length * 0.1), suggestedFix: suggestedFix(location.filePath) });
    if (locations.length === 3) break;
  }
  return locations;
}

export function create_basic_failure_analysis(data: FailureAnalysisData, projectRoot = process.cwd()): FailureAnalysis {
  return { simpleExplanation: simple_explanation(data), likelyCauses: likely_causes(data), relatedCodeLocations: related_code_locations(data, projectRoot) };
}

function valid_analysis(value: unknown, allowedLocations: Set<string>): value is FailureAnalysis {
  if (!value || typeof value !== "object") return false;
  const analysis = value as Partial<FailureAnalysis>;
  if (typeof analysis.simpleExplanation !== "string" || !analysis.simpleExplanation.trim()) return false;
  if (!Array.isArray(analysis.likelyCauses) || analysis.likelyCauses.length !== 3 || analysis.likelyCauses.some(cause => typeof cause !== "string" || !cause.trim())) return false;
  if (!Array.isArray(analysis.relatedCodeLocations) || analysis.relatedCodeLocations.length > 3) return false;
  return analysis.relatedCodeLocations.every((location, index) => location && location.rank === index + 1 && typeof location.filePath === "string" && Number.isInteger(location.lineNumber) && allowedLocations.has(`${location.filePath}:${location.lineNumber}`) && typeof location.confidence === "number" && location.confidence >= 0 && location.confidence <= 1 && typeof location.suggestedFix === "string" && Boolean(location.suggestedFix.trim()));
}

export function create_http_ai_analyzer(endpoint: string, apiKey: string): AIAnalyzer {
  return async (input, options) => {
    const instructions = "Explain the failure with words a five-year-old can understand. Return JSON with only simpleExplanation, likelyCauses (up to 3 strings), and relatedCodeLocations (up to 3 entries). Each location needs rank, filePath, lineNumber, confidence from 0 to 1, and suggestedFix. Use only the provided candidate code locations. Never invent a file path or line number.";
    const response = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${apiKey}` }, body: JSON.stringify({ model: options.model, input, instructions }), signal: AbortSignal.timeout(options.timeoutMs) });
    if (!response.ok) throw new Error(`AI provider returned ${response.status}`);
    const payload = await response.json() as unknown;
    if (!payload || typeof payload !== "object") return payload;
    const wrapped = payload as { analysis?: unknown; result?: unknown; output?: unknown };
    const value = wrapped.analysis ?? wrapped.result ?? wrapped.output ?? payload;
    if (typeof value !== "string") return value;
    try { return JSON.parse(value); } catch { return value; }
  };
}

export async function run_failure_analysis(data: FailureAnalysisData, analyzer?: AIAnalyzer, options: { model?: string; timeoutMs?: number; projectRoot?: string } = {}): Promise<FailureAnalysis> {
  const fallback = create_basic_failure_analysis(data, options.projectRoot);
  if (!analyzer) return fallback;
  const input = sanitize({ details: data.details, evidence: data.evidence, environment: data.environment, stability: data.stability, context: data.context ?? {}, candidateCodeLocations: fallback.relatedCodeLocations });
  const timeoutMs = options.timeoutMs ?? 15_000;
  const allowedLocations = new Set(fallback.relatedCodeLocations.map(location => `${location.filePath}:${location.lineNumber}`));
  try {
    const result = await Promise.race([analyzer(input, { model: options.model ?? "configured-model", timeoutMs }), new Promise<never>((_, reject) => setTimeout(() => reject(new Error("Failure analysis timed out")), timeoutMs))]);
    return valid_analysis(result, allowedLocations) ? result : fallback;
  } catch {
    return fallback;
  }
}

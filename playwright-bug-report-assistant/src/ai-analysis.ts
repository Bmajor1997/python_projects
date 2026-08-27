import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { categorize_failure } from "./fingerprint";
import { sanitize } from "./sanitizer";
import { friendly_test_name } from "./text-utils";
import type { FailureAnalysis, FailureAnalysisData, RelatedCodeLocation } from "./types";

export type AIAnalyzer = (sanitizedInput: unknown, options: { model: string; timeoutMs: number }) => Promise<unknown>;

function simple_explanation(data: FailureAnalysisData): string {
  const { details } = data;
  if (details.expectedBehavior && details.actualBehavior) return `The test expected ${details.expectedBehavior}, but it got ${details.actualBehavior} instead.`;
  const name = friendly_test_name(details.testTitle);
  const category = categorize_failure(details.errorMessage);
  if (category === "timeout") return `The ${name} test waited for something to happen, but it took too long.`;
  if (category === "selector") return `The ${name} test looked for something on the page, but it could not find it.`;
  if (category === "network" || category === "api") return `The ${name} test needed information from another service, but that request did not work.`;
  if (category === "authentication") return `The ${name} test could not prove that the user was signed in.`;
  return `The ${name} test tried to finish its job, but something went wrong.`;
}

function likely_causes(data: FailureAnalysisData): string[] {
  const causes: string[] = [];
  const category = categorize_failure(data.details.errorMessage);
  const categoryCause: Record<typeof category, string> = {
    selector: "The page element may have moved, changed its name, or not appeared.",
    timeout: "The page or action may be taking longer than the test allows.",
    authentication: "The user may not have been signed in correctly.",
    api: "An API used by the page may have returned the wrong result.",
    network: "A network request may have failed or lost its connection.",
    visual: "The page may look different from the saved visual baseline.",
    assertion: "The application returned a different value than the test expected.",
    environment: "The browser, machine, or CI environment may be configured differently.",
    unknown: "The application may not have reached the state that the test expected.",
  };
  causes.push(categoryCause[category]);
  const network = data.evidence.networkFailures[0];
  if (network) causes.push(`The ${network.method} request to ${network.url} failed${network.status ? ` with status ${network.status}` : ""}.`);
  if (data.evidence.pageErrors[0]) causes.push(`The page reported an error: ${data.evidence.pageErrors[0]}`);
  else if (data.evidence.consoleMessages[0]) causes.push(`The browser reported: ${data.evidence.consoleMessages[0]}`);
  else if (data.stability.classification === "likely flaky") causes.push("The test history changes between passing and failing, so timing or unstable data may be involved.");
  return [...new Set(causes)].slice(0, 3);
}

function valid_repository_location(path: string, lineNumber: number, projectRoot: string): { filePath: string; lineNumber: number } | null {
  const absolute = resolve(projectRoot, path);
  const repositoryPath = relative(projectRoot, absolute);
  if (repositoryPath.startsWith("..") || isAbsolute(repositoryPath) || !existsSync(absolute)) return null;
  const lineCount = readFileSync(absolute, "utf8").split(/\r?\n/).length;
  if (!Number.isInteger(lineNumber) || lineNumber < 1 || lineNumber > lineCount) return null;
  return { filePath: repositoryPath.replace(/\\/g, "/"), lineNumber };
}

function related_code_locations(data: FailureAnalysisData, projectRoot: string): RelatedCodeLocation[] {
  const candidates: Array<{ path: string; line: number }> = [{ path: data.details.testFile, line: data.details.lineNumber }];
  for (const match of data.details.stackTrace?.matchAll(/(?:\(|\bat\s+)([^()\r\n]+?\.(?:ts|tsx|js|jsx)):(\d+):\d+/g) ?? []) candidates.push({ path: match[1].trim(), line: Number(match[2]) });
  const unique = new Set<string>();
  const locations: RelatedCodeLocation[] = [];
  for (const candidate of candidates) {
    const location = valid_repository_location(candidate.path, candidate.line, projectRoot);
    if (!location) continue;
    const key = `${location.filePath}:${location.lineNumber}`;
    if (unique.has(key)) continue;
    unique.add(key);
    const rank = (locations.length + 1) as 1 | 2 | 3;
    locations.push({ rank, ...location, confidence: rank === 1 ? 0.8 : rank === 2 ? 0.65 : 0.5, suggestedFix: "Check this line against the failure evidence and update the test or application behavior that caused the mismatch." });
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
  if (!Array.isArray(analysis.likelyCauses) || analysis.likelyCauses.length > 3 || analysis.likelyCauses.some(cause => typeof cause !== "string" || !cause.trim())) return false;
  if (!Array.isArray(analysis.relatedCodeLocations) || analysis.relatedCodeLocations.length > 3) return false;
  return analysis.relatedCodeLocations.every((location, index) => location && location.rank === index + 1 && typeof location.filePath === "string" && Number.isInteger(location.lineNumber) && allowedLocations.has(`${location.filePath}:${location.lineNumber}`) && typeof location.confidence === "number" && location.confidence >= 0 && location.confidence <= 1 && typeof location.suggestedFix === "string" && Boolean(location.suggestedFix.trim()));
}

export function create_http_ai_analyzer(endpoint: string, apiKey: string): AIAnalyzer {
  return async (input, options) => {
    const instructions = "Explain the failure with words a five-year-old can understand. Return JSON with only simpleExplanation, likelyCauses (up to 3 strings), and relatedCodeLocations (up to 3 entries). Each location needs rank, filePath, lineNumber, confidence from 0 to 1, and suggestedFix. Use only the provided candidate code locations. Never invent a file path or line number.";
    const response = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${apiKey}` }, body: JSON.stringify({ model: options.model, input, instructions }), signal: AbortSignal.timeout(options.timeoutMs) });
    if (!response.ok) throw new Error(`AI provider returned ${response.status}`);
    return response.json();
  };
}

export async function run_failure_analysis(data: FailureAnalysisData, analyzer?: AIAnalyzer, options: { model?: string; timeoutMs?: number; projectRoot?: string } = {}): Promise<FailureAnalysis> {
  const fallback = create_basic_failure_analysis(data, options.projectRoot);
  if (!analyzer) return fallback;
  const input = sanitize({ details: data.details, evidence: data.evidence, environment: data.environment, stability: data.stability, candidateCodeLocations: fallback.relatedCodeLocations });
  const timeoutMs = options.timeoutMs ?? 15_000;
  const allowedLocations = new Set(fallback.relatedCodeLocations.map(location => `${location.filePath}:${location.lineNumber}`));
  try {
    const result = await Promise.race([analyzer(input, { model: options.model ?? "configured-model", timeoutMs }), new Promise<never>((_, reject) => setTimeout(() => reject(new Error("Failure analysis timed out")), timeoutMs))]);
    return valid_analysis(result, allowedLocations) ? result : fallback;
  } catch {
    return fallback;
  }
}

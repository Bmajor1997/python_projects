import { basename, join } from "node:path";
import { platform, release } from "node:os";
import { create_http_ai_analyzer, run_failure_analysis, type AIAnalyzer } from "./ai-analysis";
import { create_fingerprint } from "./fingerprint";
import { save_failure_analysis } from "./report-bundle";
import { sanitize } from "./sanitizer";
import { analyze_stability } from "./stability";
import type { FailureAnalysisData, FailureInput, GeneratedAnalysisArtifacts, ReportMode } from "./types";
import { OpenAIAnalysisProvider } from "./providers";

export type AnalyzeFailureOptions = {
  analyzer?: AIAnalyzer;
  model?: string;
  timeoutMs?: number;
  mode?: ReportMode;
  outputRoot?: string;
};

export type FailureAnalysisResult = { data: FailureAnalysisData; artifacts: GeneratedAnalysisArtifacts };

export function create_failure_analysis_data(input: FailureInput, mode: ReportMode = "developer"): FailureAnalysisData {
  const evidence = {
    screenshotPaths: [], tracePaths: [], otherAttachments: input.evidencePaths ?? [], currentUrl: null,
    consoleMessages: [], pageErrors: [], networkFailures: [], accessibilitySnapshot: null, domSnippet: null,
  };
  const environment = {
    operatingSystem: platform(), systemRelease: release(), projectName: basename(input.projectRoot) || "project",
    runtimeName: process.release.name, runtimeVersion: process.version, browserName: null, browserVersion: null,
    viewport: null, locale: null, timezone: null, executionTime: new Date(), commitSha: null, branch: null,
    ciRunUrl: null, ciProvider: process.env.CI ? "CI" : null, safeEnvironment: {},
  };
  const details = {
    testTitle: input.name, testFile: input.sourceFile ?? "", lineNumber: input.lineNumber ?? null, columnNumber: null,
    status: input.status ?? "failed", errorMessage: input.errorMessage, stackTrace: input.stackTrace ?? null,
    startTime: new Date(), durationMs: 0, retryNumber: 0, testSteps: input.steps ?? [],
    expectedBehavior: input.expectedBehavior ?? null, actualBehavior: input.actualBehavior ?? null,
    failedStep: input.steps?.at(-1) ?? null, tags: [],
  };
  const cleanDetails = sanitize(details), cleanEvidence = sanitize(evidence), cleanEnvironment = sanitize(environment);
  return {
    details: cleanDetails, evidence: cleanEvidence, environment: cleanEnvironment, generatedAt: new Date(),
    automatedWarning: "Automatically generated failure analysis. Suggested causes and fixes require verification.",
    fingerprint: create_fingerprint(cleanDetails, cleanEnvironment.runtimeName), stability: analyze_stability([]), analysis: null, mode,
    context: sanitize(input.context ?? {}), schemaVersion: "1.0", toolVersion: "1.0.0", warnings: [],
  };
}

export async function analyze_failure_data(data: FailureAnalysisData, projectRoot: string, options: AnalyzeFailureOptions = {}): Promise<FailureAnalysisResult> {
  data.analysis = await run_failure_analysis(data, options.analyzer, { model: options.model, timeoutMs: options.timeoutMs, projectRoot });
  const artifacts = await save_failure_analysis(data, options.outputRoot ?? join(projectRoot, "test-results", "failure-analyses"));
  return { data, artifacts };
}

export async function analyze_failure(input: FailureInput, options: AnalyzeFailureOptions = {}): Promise<FailureAnalysisResult> {
  const data = create_failure_analysis_data(input, options.mode);
  return analyze_failure_data(data, input.projectRoot, options);
}

export function analyzer_from_environment(env: NodeJS.ProcessEnv = process.env): AIAnalyzer | undefined {
  const provider = env.FAILURE_ANALYSIS_PROVIDER?.toLowerCase();
  if (!provider || provider === "deterministic") return undefined;
  if (provider === "openai") {
    if (!env.OPENAI_API_KEY) throw new Error("OPENAI_API_KEY is required when FAILURE_ANALYSIS_PROVIDER=openai.");
    const implementation = new OpenAIAnalysisProvider();
    const analyzer: AIAnalyzer = async (input, options) => (await implementation.analyze(input, options)).analysis;
    analyzer.providerName = "openai";
    return analyzer;
  }
  if (provider === "http") {
    if (!env.FAILURE_ANALYSIS_ENDPOINT || !env.FAILURE_ANALYSIS_API_KEY) throw new Error("FAILURE_ANALYSIS_ENDPOINT and FAILURE_ANALYSIS_API_KEY are required for the HTTP provider.");
    return create_http_ai_analyzer(env.FAILURE_ANALYSIS_ENDPOINT, env.FAILURE_ANALYSIS_API_KEY);
  }
  throw new Error(`Unsupported FAILURE_ANALYSIS_PROVIDER: ${provider}`);
}

export type ReportMode = "developer" | "product" | "customer-safe";
export type FailureCategory = "selector" | "timeout" | "authentication" | "api" | "network" | "visual" | "assertion" | "environment" | "unknown";
export type StabilityClassification = "reproducible failure" | "likely flaky" | "browser-specific" | "ci-specific" | "insufficient history" | "stable";

export type FailureDetails = {
  testTitle: string; testFile: string; lineNumber: number | null; columnNumber: number | null;
  status: string; errorMessage: string; stackTrace: string | null;
  startTime: Date; durationMs: number; retryNumber: number; testSteps: string[];
  expectedBehavior: string | null; actualBehavior: string | null; failedStep: string | null;
  tags: string[];
};
export type EvidenceFiles = {
  screenshotPaths: string[]; tracePaths: string[]; otherAttachments: string[];
  currentUrl: string | null; consoleMessages: string[]; pageErrors: string[]; networkFailures: NetworkFailure[];
  accessibilitySnapshot: unknown | null; domSnippet: string | null;
};
export type NetworkFailure = { method: string; url: string; status: number | null; reason: string | null; requestBody?: unknown; responseBody?: unknown };
export type EnvironmentDetails = {
  operatingSystem: string; systemRelease: string; projectName: string; runtimeName: string; runtimeVersion: string | null; browserName: string | null;
  browserVersion: string | null; viewport: { width: number; height: number } | null;
  locale: string | null; timezone: string | null; executionTime: Date;
  commitSha: string | null; branch: string | null; ciRunUrl: string | null; ciProvider: string | null;
  safeEnvironment: Record<string, string>;
};
export type RelatedCodeLocation = {
  rank: 1 | 2 | 3;
  filePath: string;
  lineNumber: number;
  confidence: number;
  suggestedFix: string;
};
export type FailureAnalysis = {
  simpleExplanation: string;
  likelyCauses: string[];
  relatedCodeLocations: RelatedCodeLocation[];
};
export type StabilityAnalysis = {
  classification: StabilityClassification; observations: string[]; sampleSize: number;
  failureRate: number | null; recentTrend: string; consecutivePasses: number; consecutiveFailures: number;
};
export type FailureAnalysisData = {
  details: FailureDetails; evidence: EvidenceFiles; environment: EnvironmentDetails;
  generatedAt: Date; automatedWarning: string; fingerprint: string; stability: StabilityAnalysis;
  analysis: FailureAnalysis | null; mode: ReportMode; context?: Record<string, unknown>;
};
export type FailureInput = {
  name: string;
  errorMessage: string;
  stackTrace?: string | null;
  projectRoot: string;
  sourceFile?: string | null;
  lineNumber?: number | null;
  status?: string;
  expectedBehavior?: string | null;
  actualBehavior?: string | null;
  steps?: string[];
  evidencePaths?: string[];
  context?: Record<string, unknown>;
};
export type GeneratedAnalysisArtifacts = { directory: string; data: string; markdown: string };
export type HistoryRecord = { fingerprint: string; testTitle: string; status: string; browserName: string; isCI: boolean; timestamp: string; retryNumber: number };

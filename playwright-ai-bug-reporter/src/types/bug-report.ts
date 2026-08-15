export type BugSeverity = 'Low' | 'Medium' | 'High' | 'Critical';

export interface FailureEvidence {
  testTitle: string;
  testFile: string;
  browserName: string;
  errorMessage: string;
  stackTrace?: string;
  screenshotPath?: string;
  tracePath?: string;
  timestamp: string;
}

export interface BugEnvironment {
  browser: string;
  operatingSystem: string;
  testFile: string;
}

export interface BugReport {
  title: string;
  summary: string;
  severity: BugSeverity;
  environment: BugEnvironment;
  stepsToReproduce: string[];
  expectedResult: string;
  actualResult: string;
  evidence: string[];
  generatedAt: string;
}
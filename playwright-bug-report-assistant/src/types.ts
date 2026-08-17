import type { TestCase, TestResult} from "@playwright/test/reporter";

export type FailedTest = {
  test: TestCase;
  result: TestResult
};

export type FailureDetails = {
    testTitle: string;
    testFile: string;
    lineNumber: number;
    columnNumber: number;
    status:TestResult["status" ];
    errorMessage: string;
    stackTrace: string | null;
    startTime: Date;
    durationMs: number;
    retryNumber: number;
    testSteps: string[];
};

export type EvidenceFiles = {
    screenshotPaths: string[];
    tracePaths: string[];
    videoPaths: string[];
    otherAttachments: string[];

};

export type EnvironmentDetails = {
    operatingSystem: string;
    systemRelease: string;
    projectName: string;
    browserName: string;
    executionTime: Date
};

export type HumanReview = {
    confirmedDefect: string | null;
    severity: string | null;
    priority: string | null;
    finalTitle: string | null;
    notes: string | null;
    ticketUrl: string | null;
};

export type BugReportData = {
    details: FailureDetails;
    evidence: EvidenceFiles;
    enviroment: EnvironmentDetails;
    humanReview: HumanReview;
    generatedAt: Date;
    automatedWarning: string;
};
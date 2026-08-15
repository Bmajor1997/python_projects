import type { TestCase, TestResult } from '@playwright/test/reporter';
import type { FailureEvidence } from '../types/bug-report';

export function createFailureEvidence(
  testCase: TestCase,
  testResult: TestResult
): FailureEvidence {
  const primaryError = testResult.errors[0];

  const screenshotAttachment = testResult.attachments.find(
    (attachment) =>
      attachment.name === 'screenshot' &&
      attachment.path !== undefined
  );

  const traceAttachment = testResult.attachments.find(
    (attachment) =>
      attachment.name === 'trace' &&
      attachment.path !== undefined
  );

  return {
    testTitle: testCase.titlePath().join(' > '),
    testFile: testCase.location.file,
    browserName: testCase.parent.project()?.name ?? 'Unknown',
    errorMessage:
      primaryError?.message ?? 'The test failed without an error message.',
    stackTrace: primaryError?.stack,
    screenshotPath: screenshotAttachment?.path,
    tracePath: traceAttachment?.path,
    timestamp: testResult.startTime.toISOString()
  };
}
import { join } from "node:path";

import type {
  Reporter,
  TestCase,
  TestResult,
} from "@playwright/test/reporter";

import { save_bug_report } from "./bug-report-generator";
import type { FailedTest } from "./types";

export default class BugReportReporter
implements Reporter {
  async onTestEnd(
    test: TestCase,
    result: TestResult
  ): Promise<void> {
    if (result.status === test.expectedStatus) {
      return;
    }

    const failure: FailedTest = {
      test,
      result,
    };

    const output_directory = join(
      process.cwd(),
      "test-results",
      "bug-reports"
    );

    try {
      const report_path =
        await save_bug_report(
          failure,
          output_directory,
          "markdown"
        );

      console.log(
        `Bug report saved: ${report_path}`
      );
    } catch (error) {
      const error_message =
        error instanceof Error
          ? error.message
          : String(error);

      console.error(
        `Unable to save bug report: ${error_message}`
      );
    }
  }
}
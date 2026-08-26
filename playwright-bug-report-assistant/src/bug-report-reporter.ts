import { join } from "node:path";
import type { Reporter, TestCase, TestResult } from "@playwright/test/reporter";
import { build_report_data, collect_environment, collect_failure_details, find_evidence } from "./bug-report-generator";
import { append_history, read_history } from "./history";
import type { FailedTest, ReportMode } from "./types";
import { report_formats_from_env, save_report_bundle } from "./report-bundle";

export default class BugReportReporter implements Reporter {
  async onTestEnd(test: TestCase, result: TestResult): Promise<void> {
    const mode = (process.env.BUG_REPORT_MODE ?? "developer") as ReportMode;
    if (!["developer", "product", "customer-safe"].includes(mode)) throw new Error(`Invalid BUG_REPORT_MODE: ${mode}`);
    const historyPath = join(process.cwd(), "test-results", "bug-report-history.json");
    const project = test.parent.project();
    const historyRecord = { fingerprint: "", testTitle: test.titlePath().join(" > "), status: result.status, browserName: project?.use.browserName ?? "Unknown", isCI: Boolean(process.env.CI), timestamp: new Date().toISOString(), retryNumber: result.retry };
    if (result.status === test.expectedStatus) {
      await append_history(historyPath, historyRecord).catch(error => console.error(`Unable to save test history: ${error instanceof Error ? error.message : String(error)}`));
      return;
    }
    try {
      const failure = { test, result } satisfies FailedTest;
      const history = await read_history(historyPath);
      const data = build_report_data(collect_failure_details(failure), find_evidence(result), collect_environment(failure), mode, history);
      const reports = await save_report_bundle(data, join(process.cwd(), "test-results", "bug-reports"), report_formats_from_env());
      await append_history(historyPath, { ...historyRecord, fingerprint: data.fingerprint });
      for (const [format, path] of Object.entries({ Markdown: reports.markdown, HTML: reports.html, PDF: reports.pdf })) if (path) console.log(`${format} bug report: ${path}`);
      if (reports.pdfError) console.error(`PDF bug report unavailable: ${reports.pdfError}`);
    } catch (error) { console.error(`Unable to save bug report: ${error instanceof Error ? error.message : String(error)}`); }
  }
}

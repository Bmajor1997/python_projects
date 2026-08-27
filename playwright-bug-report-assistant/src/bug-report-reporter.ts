import { join } from "node:path";
import type { Reporter, TestCase, TestResult } from "@playwright/test/reporter";
import { build_failure_analysis_data, collect_environment, collect_failure_details, find_evidence } from "./bug-report-generator";
import { append_history, read_history } from "./history";
import type { ReportMode } from "./types";
import { analyze_failure_data, analyzer_from_environment } from "./failure-analysis";

export default class BugReportReporter implements Reporter {
  private readonly pendingAnalyses = new Set<Promise<void>>();

  onTestEnd(test: TestCase, result: TestResult): void {
    const pending = this.analyzeFailure(test, result);
    this.pendingAnalyses.add(pending);
    void pending.finally(() => this.pendingAnalyses.delete(pending));
  }

  async onEnd(): Promise<void> {
    await Promise.allSettled([...this.pendingAnalyses]);
  }

  private async analyzeFailure(test: TestCase, result: TestResult): Promise<void> {
    const mode = (process.env.BUG_REPORT_MODE ?? "developer") as ReportMode;
    if (!["developer", "product", "customer-safe"].includes(mode)) throw new Error(`Invalid BUG_REPORT_MODE: ${mode}`);
    const historyPath = join(process.cwd(), "test-results", "bug-report-history.json");
    const project = test.parent.project();
    const historyRecord = { fingerprint: "", testTitle: test.titlePath().join(" > "), status: result.status, browserName: project?.use.browserName ?? "Unknown", isCI: Boolean(process.env.CI), timestamp: new Date().toISOString(), retryNumber: result.retry };
    if (result.status === test.expectedStatus || result.status === "skipped") {
      await append_history(historyPath, historyRecord).catch(error => console.error(`Unable to save test history: ${error instanceof Error ? error.message : String(error)}`));
      return;
    }
    try {
      const failure = { test, result };
      const history = await read_history(historyPath);
      const data = build_failure_analysis_data(collect_failure_details(failure), find_evidence(result), collect_environment(failure), mode, history);
      const { data: analyzed, artifacts: reports } = await analyze_failure_data(data, process.cwd(), { analyzer: analyzer_from_environment(), model: process.env.FAILURE_ANALYSIS_MODEL });
      await append_history(historyPath, { ...historyRecord, fingerprint: analyzed.fingerprint });
      console.log(`Failure analysis data: ${reports.data}`);
      console.log(`Failure summary: ${reports.markdown}`);
    } catch (error) { console.error(`Unable to save failure analysis: ${error instanceof Error ? error.message : String(error)}`); }
  }
}

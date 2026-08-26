import { format_markdown, normalize_report_data } from "./bug-report-generator";
import { friendly_report_title } from "./text-utils";
import type { BugReportData } from "./types";

export type JiraDraft = {
  projectKey: string;
  issueType: "Bug";
  summary: string;
  description: string;
  screenshotPaths: string[];
  fingerprint: string;
};

export function create_jira_draft(input: BugReportData, projectKey = "SCRUM"): JiraDraft {
  const data = normalize_report_data(input);
  return {
    projectKey,
    issueType: "Bug",
    summary: data.humanReview.finalTitle ?? data.aiAnalysis?.title ?? friendly_report_title(data.details.errorMessage, data.details.testTitle, data.details.expectedBehavior, data.details.actualBehavior),
    description: format_markdown(data),
    screenshotPaths: [...data.evidence.screenshotPaths],
    fingerprint: data.fingerprint,
  };
}

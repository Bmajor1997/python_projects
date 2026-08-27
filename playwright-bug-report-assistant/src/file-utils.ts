import type { FailureAnalysisData } from "./types";

export function make_filename(data: FailureAnalysisData): string {
  const identity = `${data.details.testTitle}-${data.environment.projectName}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48).replace(/-+$/g, "");
  return `${identity}-${data.fingerprint.slice(0, 12)}`;
}
export function make_report_folder_name(data: FailureAnalysisData): string {
  return `${make_filename(data)}-attempt-${data.details.retryNumber + 1}`;
}

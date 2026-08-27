import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import type { FailureAnalysisData } from "./types";

export async function prepare_output_folder(folder_path: string): Promise<void> { await mkdir(folder_path, { recursive: true }); }
export function make_filename(data: FailureAnalysisData): string {
  const identity = `${data.details.testTitle}-${data.environment.projectName}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48).replace(/-+$/g, "");
  return `${identity}-${data.fingerprint.slice(0, 12)}.md`;
}
export function make_report_folder_name(data: FailureAnalysisData): string {
  return `${make_filename(data).replace(/\.md$/, "")}-attempt-${data.details.retryNumber + 1}`;
}
export async function save_file(file_path: string, contents: string): Promise<void> {
  await mkdir(dirname(file_path), { recursive: true });
  await writeFile(file_path, contents, "utf8");
}

import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import type { BugReportData } from "./types";

export async function prepare_output_folder(folder_path: string): Promise<void> { await mkdir(folder_path, { recursive: true }); }
export function make_filename(data: BugReportData): string {
  const raw = `${data.details.testTitle}-${data.environment.projectName}-${data.fingerprint.slice(0, 12)}`;
  return `${raw.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "")}.md`;
}
export function make_report_folder_name(data: BugReportData): string {
  return make_filename(data).replace(/\.md$/, "");
}
export async function save_file(file_path: string, contents: string): Promise<void> {
  await mkdir(dirname(file_path), { recursive: true });
  await writeFile(file_path, contents, "utf8");
}

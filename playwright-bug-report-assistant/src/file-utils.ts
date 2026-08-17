import { mkdir, writeFile } from "node:fs/promises";
import type { BugReportData } from "./types";

// Creates the bug report output folder when it does not already exist.
export async function prepare_output_folder(
  folder_path: string
): Promise<void> {
    await mkdir(folder_path, { recursive: true });
} 

// Creates a safe and unique Markdown filename for a bug report.
export function make_filename(report_data: BugReportData): string {
    const raw_filename =
    `${report_data.details.testTitle}-${report_data.enviroment.projectName}-${report_data.generatedAt.toISOString()}`;

    const safe_filename = raw_filename
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/^-+|-+$/g, "");

    return `${safe_filename}.md`;
}


import {
  mkdir,
  writeFile,
} from "node:fs/promises";

import { dirname } from "node:path";

import type {
  BugReportData,
} from "./types";

// Creates the bug report output folder when it does not already exist.
export async function prepare_output_folder(
  folder_path: string
): Promise<void> {
    await mkdir(folder_path, { recursive: true });
} 

// Creates a safe and unique Markdown filename for a bug report.
export function make_filename(report_data: BugReportData): string {
    const raw_filename =
    `${report_data.details.testTitle}-${report_data.environment.projectName}-${report_data.generatedAt.toISOString()}`;

    const safe_filename = raw_filename
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/^-+|-+$/g, "");

    return `${safe_filename}.md`;
}

// Writes the completed Markdown report to its destination file.
export async function save_file(
  file_path: string,
  report_contents: string
): Promise<void> {
  const parent_directory =
    dirname(file_path);

  await mkdir(
    parent_directory,
    { recursive: true }
  );

  await writeFile(
    file_path,
    report_contents,
    "utf8"
  );
}
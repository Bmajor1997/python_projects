import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join, relative } from "node:path";
import { format_markdown, normalize_report_data } from "./bug-report-generator";
import { make_report_folder_name } from "./file-utils";
import type { FailureAnalysisData, GeneratedAnalysisArtifacts } from "./types";

async function localize_evidence(data: FailureAnalysisData, directory: string): Promise<FailureAnalysisData> {
  const evidenceDirectory = join(directory, "evidence");
  await mkdir(evidenceDirectory, { recursive: true });
  const used = new Map<string, number>();
  const copy = async (source: string): Promise<string> => {
    const original = basename(source) || "attachment";
    const count = used.get(original) ?? 0;
    used.set(original, count + 1);
    const dot = original.lastIndexOf(".");
    const name = count === 0 ? original : dot > 0 ? `${original.slice(0, dot)}-${count + 1}${original.slice(dot)}` : `${original}-${count + 1}`;
    const destination = join(evidenceDirectory, name);
    try {
      await copyFile(source, destination);
      return relative(directory, destination).replace(/\\/g, "/");
    } catch {
      return source.replace(/\\/g, "/");
    }
  };
  const localized = structuredClone(data);
  localized.evidence.screenshotPaths = await Promise.all(data.evidence.screenshotPaths.map(copy));
  localized.evidence.tracePaths = await Promise.all(data.evidence.tracePaths.map(copy));
  localized.evidence.otherAttachments = await Promise.all(data.evidence.otherAttachments.map(copy));
  return localized;
}

export function serialize_report_data(input: FailureAnalysisData): string {
  return JSON.stringify(normalize_report_data(input), null, 2);
}

export async function read_report_data(path: string): Promise<FailureAnalysisData> {
  const parsed = JSON.parse(await readFile(path, "utf8")) as FailureAnalysisData;
  parsed.details.startTime = new Date(parsed.details.startTime);
  parsed.environment.executionTime = new Date(parsed.environment.executionTime);
  parsed.generatedAt = new Date(parsed.generatedAt);
  return normalize_report_data(parsed);
}

export async function save_report_bundle(input: FailureAnalysisData, outputRoot: string): Promise<GeneratedAnalysisArtifacts> {
  const sanitized = normalize_report_data(input);
  const directory = join(outputRoot, make_report_folder_name(sanitized));
  await mkdir(directory, { recursive: true });
  const data = await localize_evidence(sanitized, directory);
  const artifacts: GeneratedAnalysisArtifacts = {
    directory,
    data: join(directory, "failure-analysis.json"),
    markdown: join(directory, "failure-summary.md"),
  };
  await Promise.all([
    writeFile(artifacts.data, serialize_report_data(data), "utf8"),
    writeFile(artifacts.markdown, format_markdown(data), "utf8"),
  ]);
  return artifacts;
}

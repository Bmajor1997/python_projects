import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join, relative } from "node:path";
import { format_failure_summary, normalize_failure_analysis_data } from "./failure-output";
import type { FailureAnalysisData, GeneratedAnalysisArtifacts } from "./types";

function make_filename(data: FailureAnalysisData): string {
  const identity = `${data.details.testTitle}-${data.environment.projectName}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48).replace(/-+$/g, "");
  return `${identity}-${data.fingerprint.slice(0, 12)}`;
}

export function make_failure_analysis_folder_name(data: FailureAnalysisData): string {
  return `${make_filename(data)}-attempt-${data.details.retryNumber + 1}`;
}

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

export function serialize_failure_analysis_data(input: FailureAnalysisData): string {
  return JSON.stringify(normalize_failure_analysis_data(input), null, 2);
}

export async function read_failure_analysis_data(path: string): Promise<FailureAnalysisData> {
  const parsed = JSON.parse(await readFile(path, "utf8")) as FailureAnalysisData;
  parsed.details.startTime = new Date(parsed.details.startTime);
  parsed.environment.executionTime = new Date(parsed.environment.executionTime);
  parsed.generatedAt = new Date(parsed.generatedAt);
  return normalize_failure_analysis_data(parsed);
}

export async function save_failure_analysis(input: FailureAnalysisData, outputRoot: string): Promise<GeneratedAnalysisArtifacts> {
  const sanitized = normalize_failure_analysis_data(input);
  const directory = join(outputRoot, make_failure_analysis_folder_name(sanitized));
  await mkdir(directory, { recursive: true });
  const data = await localize_evidence(sanitized, directory);
  const artifacts: GeneratedAnalysisArtifacts = {
    directory,
    data: join(directory, "failure-analysis.json"),
    markdown: join(directory, "failure-summary.md"),
  };
  await Promise.all([
    writeFile(artifacts.data, serialize_failure_analysis_data(data), "utf8"),
    writeFile(artifacts.markdown, format_failure_summary(data), "utf8"),
  ]);
  return artifacts;
}

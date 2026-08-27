import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { analyze_failure, analyzer_from_environment } from "./failure-analysis";
import type { FailureInput } from "./types";

async function main(): Promise<void> {
  const inputPath = process.argv[2];
  let source: string;
  if (inputPath) source = await readFile(resolve(inputPath), "utf8");
  else {
    const chunks: Buffer[] = [];
    for await (const chunk of process.stdin) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    source = Buffer.concat(chunks).toString("utf8");
  }
  const input = JSON.parse(source) as Partial<FailureInput>;
  if (typeof input.name !== "string" || typeof input.errorMessage !== "string") throw new Error("Failure input requires name and errorMessage.");
  const completeInput = { ...input, projectRoot: typeof input.projectRoot === "string" ? resolve(input.projectRoot) : process.cwd() } as FailureInput;
  const result = await analyze_failure(completeInput, { analyzer: analyzer_from_environment(), model: process.env.FAILURE_ANALYSIS_MODEL });
  process.stdout.write(`${JSON.stringify({ analysis: result.data.analysis, artifacts: result.artifacts }, null, 2)}\n`);
}

void main().catch(error => { console.error(error instanceof Error ? error.message : String(error)); process.exitCode = 1; });

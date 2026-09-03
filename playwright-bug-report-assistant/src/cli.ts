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
  const input: Partial<FailureInput> = JSON.parse(source) as Partial<FailureInput>;
  if (typeof input.name !== "string" || !input.name.trim()) throw new Error("Invalid input at name: expected a non-empty string.");
  if (typeof input.errorMessage !== "string" || !input.errorMessage.trim()) throw new Error("Invalid input at errorMessage: expected a non-empty string.");
  if (input.steps !== undefined && (!Array.isArray(input.steps) || input.steps.some(step => typeof step !== "string"))) throw new Error("Invalid input at steps: expected an array of strings.");
  if (input.lineNumber !== undefined && input.lineNumber !== null && (!Number.isInteger(input.lineNumber) || input.lineNumber < 1)) throw new Error("Invalid input at lineNumber: expected a positive integer.");
  const completeInput = { ...input, projectRoot: typeof input.projectRoot === "string" ? resolve(input.projectRoot) : process.cwd() } as FailureInput;
  const timeoutMs = process.env.FAILURE_ANALYSIS_TIMEOUT_MS ? Number(process.env.FAILURE_ANALYSIS_TIMEOUT_MS) : undefined;
  if (timeoutMs !== undefined && (!Number.isFinite(timeoutMs) || timeoutMs <= 0)) throw new Error("Invalid configuration at FAILURE_ANALYSIS_TIMEOUT_MS: expected a positive number.");
  const result = await analyze_failure(completeInput, { analyzer: analyzer_from_environment(), model: process.env.FAILURE_ANALYSIS_MODEL, timeoutMs });
  process.stdout.write(`${JSON.stringify({ analysis: result.data.analysis, artifacts: result.artifacts }, null, 2)}\n`);
}

void main().catch(error => { console.error(process.env.FAILURE_ANALYSIS_DEBUG === "true" && error instanceof Error ? error.stack : error instanceof Error ? error.message : String(error)); process.exitCode = 1; });

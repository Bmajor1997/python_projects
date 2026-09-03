import OpenAI from "openai";
import type { FailureAnalysis } from "./types";

export type AnalysisProviderResult = { analysis: unknown; provider: string; model: string };
export interface AnalysisProvider {
  readonly name: string;
  analyze(input: unknown, options: { model: string; timeoutMs: number }): Promise<AnalysisProviderResult>;
}

const ANALYSIS_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["simpleExplanation", "likelyCauses", "relatedCodeLocations"],
  properties: {
    simpleExplanation: { type: "string" },
    likelyCauses: { type: "array", minItems: 1, maxItems: 3, items: { type: "string" } },
    relatedCodeLocations: { type: "array", maxItems: 3, items: { type: "object", additionalProperties: false, required: ["rank", "filePath", "lineNumber", "confidence", "suggestedFix"], properties: { rank: { type: "integer", minimum: 1, maximum: 3 }, filePath: { type: "string" }, lineNumber: { type: "integer", minimum: 1 }, confidence: { type: "number", minimum: 0, maximum: 1 }, suggestedFix: { type: "string" } } } },
  },
} as const;

export class OpenAIAnalysisProvider implements AnalysisProvider {
  readonly name = "openai";
  constructor(private readonly client = new OpenAI()) {}
  async analyze(input: unknown, options: { model: string; timeoutMs: number }): Promise<AnalysisProviderResult> {
    const response = await this.client.responses.create({
      model: options.model,
      store: false,
      instructions: "Analyze this software failure for a developer. Be concise, evidence-based, and technically useful. Use only candidate code locations supplied in the input; never invent a path or line number.",
      input: JSON.stringify(input),
      text: { format: { type: "json_schema", name: "failure_analysis", strict: true, schema: ANALYSIS_SCHEMA } },
    }, { timeout: options.timeoutMs });
    return { analysis: JSON.parse(response.output_text) as FailureAnalysis, provider: this.name, model: options.model };
  }
}

export class HttpAnalysisProvider implements AnalysisProvider {
  readonly name = "http";
  constructor(private readonly endpoint: string, private readonly apiKey: string) {}
  async analyze(input: unknown, options: { model: string; timeoutMs: number }): Promise<AnalysisProviderResult> {
    const response = await fetch(this.endpoint, { method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${this.apiKey}` }, body: JSON.stringify({ model: options.model, input, schema: ANALYSIS_SCHEMA }), signal: AbortSignal.timeout(options.timeoutMs) });
    if (!response.ok) throw new Error(`Analysis provider returned HTTP ${response.status}`);
    const payload = await response.json() as { analysis?: unknown; result?: unknown; output?: unknown };
    let analysis = payload.analysis ?? payload.result ?? payload.output ?? payload;
    if (typeof analysis === "string") analysis = JSON.parse(analysis);
    return { analysis, provider: this.name, model: options.model };
  }
}

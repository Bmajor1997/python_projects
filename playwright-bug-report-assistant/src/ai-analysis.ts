import type { AIAnalysis, FailureAnalysisData } from "./types";
import { sanitize } from "./sanitizer";

export type AIAnalyzer = (sanitizedInput: unknown, options: { model: string; timeoutMs: number }) => Promise<AIAnalysis>;
export function create_http_ai_analyzer(endpoint: string, apiKey: string): AIAnalyzer {
  return async (input, options) => {
    const response = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${apiKey}` }, body: JSON.stringify({ model: options.model, input, instructions: "Return JSON matching AIAnalysis. Separate verified facts, assumptions, and missing information. Do not present hypotheses as facts." }), signal: AbortSignal.timeout(options.timeoutMs) });
    if (!response.ok) throw new Error(`AI provider returned ${response.status}`);
    const value = await response.json() as AIAnalysis;
    if (!value || typeof value.title !== "string" || !Array.isArray(value.assumptions) || typeof value.confidence !== "number") throw new Error("AI provider returned an invalid analysis");
    return value;
  };
}
export async function run_ai_analysis(data: FailureAnalysisData, analyzer: AIAnalyzer | undefined, options: { enabled: boolean; model?: string; timeoutMs?: number }): Promise<AIAnalysis | null> {
  if (!options.enabled || !analyzer) return null;
  const input = sanitize({ details: data.details, evidence: data.evidence, environment: data.environment, stability: data.stability });
  const timeoutMs = options.timeoutMs ?? 15_000;
  try {
    return await Promise.race([analyzer(input, { model: options.model ?? "configured-model", timeoutMs }), new Promise<never>((_, reject) => setTimeout(() => reject(new Error("AI analysis timed out")), timeoutMs))]);
  } catch { return null; }
}

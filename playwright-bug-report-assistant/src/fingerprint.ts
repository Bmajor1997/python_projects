import { createHash } from "node:crypto";
import type { FailureDetails, FailureCategory } from "./types";

export function categorize_failure(message: string): FailureCategory {
  const text = message.toLowerCase();
  if (/timeout|timed out/.test(text)) return "timeout";
  if (/locator|selector|strict mode/.test(text)) return "selector";
  if (/401|403|unauthori[sz]ed|login|authentication/.test(text)) return "authentication";
  if (/request|response|\b5\d\d\b|api/.test(text)) return "api";
  if (/network|econn|dns|socket/.test(text)) return "network";
  if (/snapshot|pixel|visual/.test(text)) return "visual";
  if (/expect|assert/.test(text)) return "assertion";
  if (/browser.*closed|executable|environment/.test(text)) return "environment";
  return "unknown";
}
export function normalize_failure_text(value: string): string {
  return value.toLowerCase().replace(/[a-f\d]{8}-[a-f\d-]{27,}/gi, "<uuid>").replace(/\b\d{10,}\b/g, "<number>").replace(/:\d+:\d+/g, ":<line>").replace(/\\/g, "/").replace(/\s+/g, " ").trim();
}
export function create_fingerprint(details: FailureDetails, browserName: string, url?: string | null): string {
  const firstFrame = details.stackTrace?.split("\n").find(line => line.includes("at ")) ?? "";
  const input = [details.testTitle, categorize_failure(details.errorMessage), normalize_failure_text(details.errorMessage), normalize_failure_text(firstFrame), url ? new URL(url).pathname : "", browserName].join("|");
  return createHash("sha256").update(input).digest("hex");
}

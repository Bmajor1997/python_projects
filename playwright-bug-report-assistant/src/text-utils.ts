import { stripVTControlCharacters } from "node:util";
export function clean_error_text(value: string): string { return stripVTControlCharacters(value).trim(); }
export function expectation_values(value: string): { expected: string; received: string } | null {
  const expected = value.match(/Expected:\s*(?:"([^"]+)"|([^\r\n]+))/i)?.slice(1).find(Boolean)?.trim();
  const received = value.match(/Received:\s*(?:"([^"]+)"|([^\r\n]+))/i)?.slice(1).find(Boolean)?.trim();
  return expected && received ? { expected, received } : null;
}
export function friendly_failure_message(value: string): string {
  const comparison = expectation_values(value);
  if (comparison) return `Expected the page to say "${comparison.expected}", but it said "${comparison.received}".`;
  return clean_error_text(value).replace(/^error:\s*/i, "").split(/\r?\n/)[0] || "The test did not work as expected.";
}
export function friendly_report_title(value: string, fallbackTestTitle: string, expected?: string | null, received?: string | null): string {
  const comparison = expectation_values(value) ?? (expected && received ? { expected, received } : null);
  if (comparison) return `Problem: "${comparison.received}" appeared instead of "${comparison.expected}"`;
  const simpleTestName = fallbackTestTitle.split(" > ").map(part => part.trim()).filter(Boolean).at(-1) ?? "Test problem";
  return `Problem found: ${simpleTestName}`;
}
export function friendly_test_name(value: string): string {
  return value.split(" > ").map(part => part.trim()).filter(Boolean).at(-1) ?? value;
}
export function escape_markdown(value: string): string { return value.replace(/([\\`*_{}\[\]<>()#+\-.!|>])/g, "\\$1"); }
export function log_error(operation: string, error: unknown): void {
  console.error(`[Bug Report Assistant] ${operation}: ${error instanceof Error ? error.message : String(error)}`);
}

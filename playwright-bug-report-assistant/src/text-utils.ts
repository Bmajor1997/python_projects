import { stripVTControlCharacters } from "node:util";
export function clean_error_text(value: string): string { return stripVTControlCharacters(value).trim(); }
export function escape_markdown(value: string): string { return value.replace(/([\\`*_{}\[\]<>()#+\-.!|>])/g, "\\$1"); }
export function log_error(operation: string, error: unknown): void {
  console.error(`[Bug Report Assistant] ${operation}: ${error instanceof Error ? error.message : String(error)}`);
}

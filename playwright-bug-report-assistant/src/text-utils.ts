import { stripVTControlCharacters } from "node:util";

// Removes unnecessary terminal formatting while preserving the original error information.
export function clean_error_text(error_text: string): string {
    const text_without_codes = stripVTControlCharacters(error_text)
    return text_without_codes.trim();
}

// Escapes special characters that could accidentally change the Markdown layout.
export function escape_markdown(text: string): string {
    const markdown_characters = /([\\`*_{}\[\]<>()#+\-.!|>])/g;

    return text.replace(markdown_characters, "\\$1");
}

// Displays a clear terminal message when the Bug Report Assistant encounters an error.
export function log_error(operation: string, error: unknown): void {
     const error_message =
        error instanceof Error ? error.message : String(error);
      console.error(
  `[Bug Report Assistant] ${operation}: ${error_message}`
);
}
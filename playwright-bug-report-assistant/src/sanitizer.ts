const DEFAULT_KEYS = /^(authorization|proxy-authorization|cookie|set-cookie|password|passwd|secret|token|access[_-]?token|api[_-]?key|session|credit[_-]?card|ssn)$/i;
const TOKEN_PATTERNS = [
  /\bBearer\s+[A-Za-z0-9._~+\/-]+=*/gi,
  /\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{12,}\b/g,
];
export type SanitizerOptions = { sensitiveKeys?: RegExp; customPatterns?: RegExp[]; maxStringLength?: number; allowedEnvironmentKeys?: string[] };
const REDACTED = "[REDACTED]";

export function sanitize_string(value: string, options: SanitizerOptions = {}): string {
  let clean = value;
  for (const pattern of [...TOKEN_PATTERNS, ...(options.customPatterns ?? [])]) clean = clean.replace(pattern, REDACTED);
  try {
    const url = new URL(clean);
    for (const key of [...url.searchParams.keys()]) if ((options.sensitiveKeys ?? DEFAULT_KEYS).test(key)) url.searchParams.set(key, REDACTED);
    clean = url.toString();
  } catch { /* ordinary text */ }
  const max = options.maxStringLength ?? 10_000;
  return clean.length > max ? `${clean.slice(0, max)}…[TRUNCATED]` : clean;
}

export function sanitize<T>(value: T, options: SanitizerOptions = {}, seen = new WeakSet<object>()): T {
  if (typeof value === "string") return sanitize_string(value, options) as T;
  if (value === null || typeof value !== "object") return value;
  if (seen.has(value)) return "[CIRCULAR]" as T;
  seen.add(value);
  if (Array.isArray(value)) return value.map(item => sanitize(item, options, seen)) as T;
  const output: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) output[key] = (options.sensitiveKeys ?? DEFAULT_KEYS).test(key) ? REDACTED : sanitize(item, options, seen);
  return output as T;
}

export function safe_environment(env: NodeJS.ProcessEnv, allowlist: string[]): Record<string, string> {
  return Object.fromEntries(allowlist.flatMap(key => env[key] === undefined ? [] : [[key, sanitize_string(env[key]!)]]));
}

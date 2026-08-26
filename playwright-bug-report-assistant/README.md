# Playwright Bug Report Assistant

This custom Playwright reporter produces deterministic, sanitized Markdown reports and preserves Playwright screenshots, traces, and videos as separate artifacts.

## Setup

```sh
npm ci
npx playwright install chromium
npm test
```

Use `src/fixtures.ts` instead of importing `test` directly from Playwright when you want console errors, page exceptions, failed responses, URL, DOM, and accessibility context captured. The reporter still works without the fixture and degrades to attachment-only evidence.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BUG_REPORT_MODE` | `developer` | `developer`, `product`, or `customer-safe` |
| `BUG_REPORT_SAFE_ENV` | `CI,NODE_ENV` | Comma-separated environment-variable allowlist |

Reports are written to `test-results/bug-reports`. History is stored in `test-results/bug-report-history.json`. Large evidence remains in Playwright's output directory and is linked rather than embedded.

## Security and privacy

All structured runtime context passes through recursive sanitization before being attached or formatted. Authorization data, cookies, passwords, tokens, API keys, sensitive URL parameters, and token-shaped strings are redacted. Environment variables are denied by default except for the explicit allowlist. Customer-safe mode additionally removes stack traces, internal paths, request details, DOM content, accessibility content, source revision data, and diagnostic logs.

Captured request and response bodies are intentionally disabled by default because they are unusually likely to contain private data. Projects that add them to `bug-report-context` must sanitize and size-limit them first.

## Stability and duplicates

Reports use a SHA-256 fingerprint derived from normalized test identity, category, error, relevant stack frame, route, and browser. UUIDs, timestamps, large numeric IDs, and source line numbers are normalized. Historical results support evidence-backed classifications. With fewer than three samples, the reporter says that history is insufficient.

## Optional integrations

`src/ai-analysis.ts` exposes an `AIAnalyzer` interface. It accepts only the sanitized report payload, applies a timeout, and safely falls back to a normal report. Keep AI disabled unless your organization has approved the provider and data policy. AI output is labeled as requiring human review.

`src/publisher.ts` provides an idempotent GitHub Issues adapter and a provider-neutral interface for Jira or Linear adapters. Use dry-run mode before publishing. Never provide publishing or AI credentials to pull-request workflows from forks.

## Limitations

- Reporters cannot directly access a live `Page`; rich runtime evidence requires the supplied automatic fixture.
- Browser version is unavailable through the reporter API alone.
- Visual baseline comparison uses Playwright's built-in screenshot assertions and project baselines.
- Jira and Linear need organization-specific field mappings; their common adapter interface is included, not concrete mappings.

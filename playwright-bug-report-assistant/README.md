# Playwright Failure Analysis Assistant

This project is an automation-only Playwright failure analysis assistant. Its custom reporter reacts to failed Playwright tests and collects sanitized diagnostic data, including failure details, screenshots, traces, runtime context, environment and CI metadata, fingerprints, history, and stability analysis.

The future analysis schema and likely-code-location recommendations are intentionally not implemented yet. Existing report formats remain as transitional automated outputs.

## Setup

```sh
npm ci
npx playwright install chromium
npm test
```

Use `src/fixtures.ts` instead of importing `test` directly from Playwright when console warnings and errors, page exceptions, failed responses, current URL, DOM, and accessibility context should be captured. The reporter still works without the fixture and degrades to attachment-only evidence.

## Automated flow

The reporter is registered in `playwright.config.ts`:

```text
Playwright test runs
→ test fails
→ custom reporter receives the failure
→ failure, evidence, environment, fingerprint, history, and stability data are collected
→ enabled transitional report files are written
```

Reports are written to `test-results/bug-reports/<test-project-fingerprint>/`. History is stored in `test-results/bug-report-history.json`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BUG_REPORT_MODE` | `developer` | `developer`, `product`, or `customer-safe` |
| `BUG_REPORT_SAFE_ENV` | `CI,NODE_ENV` | Comma-separated environment-variable allowlist |
| `BUG_REPORT_MARKDOWN` | `true` | Enable or disable Markdown output |
| `BUG_REPORT_HTML` | `true` | Enable or disable HTML output |
| `BUG_REPORT_PDF` | `true` | Enable or disable best-effort PDF output |
| `BUG_REPORT_DOCX` | `true` | Enable or disable Word output |

`bug-report-data.json` is the persisted, sanitized `FailureAnalysisData` payload. Evidence is copied when possible and always linked; large traces are never embedded. PDF and DOCX generation are best-effort and do not replace the original Playwright failure as the authoritative test result.

## Security and privacy

All formats are rendered from the same recursively sanitized payload. Authorization data, cookies, passwords, tokens, API keys, sensitive URL parameters, and token-shaped strings are redacted. Environment variables are denied by default except for the explicit allowlist. Customer-safe mode additionally removes stack traces, internal paths, request details, DOM content, accessibility content, source revision data, and diagnostic logs.

Captured request and response bodies are disabled by default because they are likely to contain private data. Projects that add them to `bug-report-context` must sanitize and size-limit them first.

## Stability and optional AI analysis

Failures use a SHA-256 fingerprint derived from normalized test identity, category, error, relevant stack frame, route, and browser. Historical results support evidence-backed stability classifications; fewer than three samples are reported as insufficient history.

`src/ai-analysis.ts` exposes the existing transitional `AIAnalyzer` interface. It accepts only the sanitized failure-analysis payload, applies a timeout, and safely falls back when unavailable. The final AI failure-analysis schema will be designed separately.

## Limitations

- Reporters cannot directly access a live `Page`; rich runtime evidence requires the supplied automatic fixture.
- Browser version is unavailable through the reporter API alone.
- Visual baseline comparison uses Playwright's built-in screenshot assertions and project baselines.

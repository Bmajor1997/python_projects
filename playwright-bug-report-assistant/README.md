# Playwright Bug Report Assistant

This project combines a custom Playwright reporter with a Windows desktop workflow for manual testers. Every failure gets its own folder under `test-results/bug-reports`, with deterministic, sanitized `bug-report.md`, `bug-report.html`, `bug-report.pdf`, `bug-report.docx`, and `bug-report-data.json` files plus an `evidence` folder containing copied screenshots, traces, and other attachments. Video recording and video evidence are intentionally disabled.

## Setup

```sh
npm ci
npx playwright install chromium
npm test
```

## Windows desktop application

Run the application locally during development:

```sh
npm run desktop:start
```

The interface lets a manual tester choose an approved scenario, run it, review the sanitized failure, complete the human-review fields, regenerate every enabled report, open exported files, and preview a Jira Bug for project `SCRUM`. Live Jira publishing is intentionally disabled until OAuth is implemented.

Approved scenarios live in `manual-scenarios.json`. Each entry has a stable ID, friendly name and description, test file, exact Playwright test name, and Playwright project. Only entries in this file can be launched through the desktop application. Paths outside the application are rejected. The included payment-status scenario is skipped during the normal suite and runs only when launched by the desktop application.

Build an installable Windows package with:

```sh
npm run desktop:package
```

This command downloads a package-local Playwright Chromium build and creates an NSIS installer under `release/`. Installed reports are stored in the user's Documents folder under `Playwright Bug Report Assistant`; source files and credentials are not required by a manual tester.

Use `src/fixtures.ts` instead of importing `test` directly from Playwright when you want console errors, page exceptions, failed responses, URL, DOM, and accessibility context captured. The reporter still works without the fixture and degrades to attachment-only evidence.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BUG_REPORT_MODE` | `developer` | `developer`, `product`, or `customer-safe` |
| `BUG_REPORT_SAFE_ENV` | `CI,NODE_ENV` | Comma-separated environment-variable allowlist |
| `BUG_REPORT_MARKDOWN` | `true` | Enable or disable Markdown output (`true`/`false`) |
| `BUG_REPORT_HTML` | `true` | Enable or disable HTML output (`true`/`false`) |
| `BUG_REPORT_PDF` | `true` | Enable or disable best-effort PDF output (`true`/`false`) |
| `BUG_REPORT_DOCX` | `true` | Enable or disable editable Word output (`true`/`false`) |

Reports are written to `test-results/bug-reports/<test-project-fingerprint>/`. History is stored in `test-results/bug-report-history.json`. Evidence is copied when possible and always linked; large traces are never embedded in HTML or PDF. PDF generation uses HTML internally, but a successfully rendered temporary HTML source is removed when HTML output is disabled.

`bug-report-data.json` is the persisted, sanitized source of truth used by the desktop editor. Saving a review sanitizes the reviewer-entered values again and regenerates the enabled formats. Do not replace it with raw Playwright output.

PDF creation uses the installed Playwright Chromium browser. It is deliberately best-effort: a missing browser or rendering error is printed as a concise warning while the HTML and Markdown reports remain available and the original Playwright failure remains authoritative.

Human-review fields display `Pending Review` until a custom value is supplied in `humanReview`. In the HTML report, reviewers can click any review value and type replacement wording, then print or save the edited page. Markdown is directly editable as text. The automatically generated PDF is a static snapshot; edit the HTML or report data and regenerate/print when a revised PDF is needed.

The Word report is fully editable. Open `bug-report.docx` in Microsoft Word or LibreOffice, or upload it to Google Docs, then replace any `Pending Review` value and save normally. Screenshots are embedded; traces and other large evidence remain separate linked files, so keep the sibling `evidence` folder when moving a report. DOCX generation is independent and best-effort: an error does not remove other formats or affect the original test failure.

## Security and privacy

All formats are rendered from the same recursively sanitized report payload. HTML metacharacters are escaped at render time. Authorization data, cookies, passwords, tokens, API keys, sensitive URL parameters, and token-shaped strings are redacted. Environment variables are denied by default except for the explicit allowlist. Customer-safe mode additionally removes stack traces, internal paths, request details, DOM content, accessibility content, source revision data, and diagnostic logs.

Captured request and response bodies are intentionally disabled by default because they are unusually likely to contain private data. Projects that add them to `bug-report-context` must sanitize and size-limit them first.

## Stability and duplicates

Reports use a SHA-256 fingerprint derived from normalized test identity, category, error, relevant stack frame, route, and browser. UUIDs, timestamps, large numeric IDs, and source line numbers are normalized. Historical results support evidence-backed classifications. With fewer than three samples, the reporter says that history is insufficient.

## Optional integrations

`src/ai-analysis.ts` exposes an `AIAnalyzer` interface. It accepts only the sanitized report payload, applies a timeout, and safely falls back to a normal report. Keep AI disabled unless your organization has approved the provider and data policy. AI output is labeled as requiring human review.

`src/jira-draft.ts` creates a sanitized Jira preview for project `SCRUM` and issue type `Bug`; screenshots are identified for later attachment. Live Jira access is not implemented yet. The planned integration will use Atlassian OAuth, keep tokens in protected Windows storage, preview the final ticket, and require confirmation before publishing. `src/publisher.ts` retains the existing provider-neutral interface and GitHub adapter for compatibility.

## Limitations

- Reporters cannot directly access a live `Page`; rich runtime evidence requires the supplied automatic fixture.
- Browser version is unavailable through the reporter API alone.
- Visual baseline comparison uses Playwright's built-in screenshot assertions and project baselines.
- Jira OAuth and live issue creation are deferred; the current desktop application creates a Jira-ready preview only.
- The Windows installer is large because Electron and Playwright Chromium are packaged with the application.

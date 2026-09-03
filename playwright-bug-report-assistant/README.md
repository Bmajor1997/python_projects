# Playwright Failure Analysis Assistant

A privacy-aware developer tool for Playwright and CI workflows. It collects failure evidence, identifies likely causes, validates source locations, and writes portable JSON and Markdown reports. It works offline and can optionally enhance reports with OpenAI.

## Features

- Playwright reporter and optional evidence fixture
- Generic CLI and TypeScript API
- Deterministic analysis without an API key
- OpenAI Responses API integration with strict structured output
- Generic HTTP provider
- Repository-verified code locations; invented paths are rejected
- Developer, product, and customer-safe modes
- Secret and email redaction, bounded evidence, and opt-in DOM capture
- Failure fingerprints and history-based stability analysis

## Architecture

```text
Playwright / CLI / TypeScript API
              ↓
   normalized, sanitized failure
              ↓
 deterministic candidate analysis
       ↙              ↘
 no provider         AI provider
       ↘              ↙
      validated final result
              ↓
 JSON + Markdown + local evidence
```

The shared core does not depend on Playwright. If a provider is unavailable or returns invalid output, the report records the fallback and uses deterministic analysis.

## Requirements and setup

- Node.js 20+
- Playwright 1.50+ for the Playwright adapter

```sh
npm ci
npx playwright install chromium
npm run typecheck
npm test
```

## Playwright setup

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  reporter: [["list"], ["playwright-bug-report-assistant/reporter"]],
  use: { screenshot: "only-on-failure", trace: "retain-on-failure" },
});
```

For console errors, failed requests, current URL, and optional page context:

```ts
import { test, expect } from "playwright-bug-report-assistant/playwright";
```

Reports are written under `test-results/failure-analyses/`.

## CLI and API

```json
{
  "name": "Import customer data",
  "errorMessage": "FileNotFoundError: customers.csv was not found",
  "projectRoot": "C:/projects/example",
  "sourceFile": "C:/projects/example/import.py",
  "lineNumber": 18
}
```

```sh
failure-analysis failure.json
```

During development use `npm run analyze -- failure.json`. The CLI also accepts JSON through standard input.

```ts
import { analyzeFailure } from "playwright-bug-report-assistant";

const result = await analyzeFailure({
  name: "Invoice import",
  errorMessage: "CSV header is missing",
  projectRoot: process.cwd(),
});
```

## OpenAI

The OpenAI provider uses the Responses API with strict JSON Schema output. Tests and CI use no live API calls.

```env
FAILURE_ANALYSIS_PROVIDER=openai
OPENAI_API_KEY=your-key
FAILURE_ANALYSIS_MODEL=your-supported-model
FAILURE_ANALYSIS_TIMEOUT_MS=15000
```

When the provider is unset or `deterministic`, no failure data leaves the machine. A custom HTTP provider uses `FAILURE_ANALYSIS_PROVIDER=http`, `FAILURE_ANALYSIS_ENDPOINT`, and `FAILURE_ANALYSIS_API_KEY`; it receives `{ model, input, schema }`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BUG_REPORT_MODE` | `developer` | `developer`, `product`, or `customer-safe` |
| `BUG_REPORT_SAFE_ENV` | `CI,NODE_ENV` | Environment allowlist |
| `FAILURE_ANALYSIS_PROVIDER` | `deterministic` | `deterministic`, `openai`, or `http` |
| `FAILURE_ANALYSIS_MODEL` | `configured-model` | Provider model |
| `FAILURE_ANALYSIS_TIMEOUT_MS` | `15000` | Provider timeout |
| `FAILURE_ANALYSIS_CAPTURE_DOM` | `false` | Opt in to a limited DOM snippet |
| `FAILURE_ANALYSIS_CAPTURE_ACCESSIBILITY` | `false` | Opt in to an ARIA snapshot |
| `FAILURE_ANALYSIS_DEBUG` | `false` | Show CLI stack traces |

## Privacy and evidence

- Provider input is recursively sanitized; common credentials, tokens, sensitive URL parameters, and emails are redacted.
- DOM and accessibility capture are disabled by default.
- Screenshots, traces, and attachments remain local and are never included in provider input.
- Customer-safe reports omit internal paths, stack traces, diagnostics, context, screenshots, traces, and attachments.
- Text and event collections are bounded. Automated redaction cannot identify every kind of private data, so review artifacts before sharing.

Each report contains versioned JSON, Markdown, copied evidence, provider/model metadata, fallback state, and structured warnings.

## Stability labels

- `insufficient history`: fewer than three comparable observations
- `likely flaky`: alternating outcomes or a retry that passed
- `browser-specific`: failures isolated to one of multiple browsers
- `ci-specific`: CI failures while a local observation passed
- `reproducible failure`: every comparable observation failed
- `stable`: enough history without those patterns

These are evidence summaries, not proof of root cause.

## Build and package

```sh
npm run build
npm run pack:check
```

Exports: API at `.`, reporter at `./reporter`, and fixture at `./playwright`.

## Demo, security, and limitations

See [docs/demo-script.md](docs/demo-script.md) and [examples/sample-report.md](examples/sample-report.md). All examples use synthetic data, not client work. See [SECURITY.md](SECURITY.md) before sharing artifacts.

The current analyzer validates stack/test locations rather than semantically searching every repository file. History is a process-local JSON store. Redaction reduces risk but is not a guarantee. Live OpenAI verification requires the owner’s credentials and is intentionally excluded from CI.

The project is prepared as a v1.0 release candidate. Publishing and release creation require the repository owner’s explicit approval.

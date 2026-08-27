# Failure Analysis Assistant

This project analyzes failures from scripts, applications, tests, and CI jobs. Playwright is supported through an adapter, but the shared analysis core does not depend on Playwright.

Each failure receives a short explanation in very simple language, three likely causes, and up to three trustworthy repository code locations. Every location includes an exact line number, confidence score, and suggested fix. The assistant returns fewer locations rather than inventing files or line numbers.

## Setup

```sh
npm ci
npx playwright install chromium
npm test
```

## Analyze any failure

Create a JSON input file:

```json
{
  "name": "Import customer data",
  "errorMessage": "FileNotFoundError: customers.csv was not found",
  "stackTrace": "File \"C:/projects/example/import.py\", line 18, in load_customers",
  "projectRoot": "C:/projects/example",
  "sourceFile": "C:/projects/example/import.py",
  "lineNumber": 18
}
```

Run:

```sh
npm run analyze -- failure.json
```

The CLI also accepts the same JSON through standard input. Code can call `analyze_failure()` from `src/failure-analysis.ts` directly.

The generic input supports a name, error message, stack trace, project root, optional source location, status, expected and actual values, steps, evidence paths, and additional context. Common JavaScript, TypeScript, Python, C#, Java, Go, Ruby, PHP, Rust, C, and C++ stack locations are recognized when they contain repository-resolvable paths.

## Playwright adapter

The custom reporter remains registered in `playwright.config.ts`:

```text
Playwright test fails
→ Playwright adapter collects browser evidence
→ shared failure-analysis core runs
→ JSON, Markdown, and evidence artifacts are written
```

Use `src/fixtures.ts` when console warnings and errors, page exceptions, failed responses, current URL, DOM, and accessibility context should be captured. The reporter still works without the fixture.

## Output

Artifacts are written under `test-results/failure-analyses/` by default:

- `failure-analysis.json`
- `failure-summary.md`
- Copied evidence files

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BUG_REPORT_MODE` | `developer` | Transitional Playwright disclosure mode |
| `BUG_REPORT_SAFE_ENV` | `CI,NODE_ENV` | Playwright environment-variable allowlist |
| `FAILURE_ANALYSIS_ENDPOINT` | unset | Optional HTTP analysis-provider endpoint |
| `FAILURE_ANALYSIS_API_KEY` | unset | API key used with the optional endpoint |
| `FAILURE_ANALYSIS_MODEL` | `configured-model` | Optional provider model name |

Without an external provider, the shared engine creates a baseline analysis from the error, evidence, source location, and stack trace. Provider output is accepted only when it follows the small analysis schema and uses locations already verified against the repository.

## Security

Artifacts and provider inputs are recursively sanitized. Authorization data, cookies, passwords, tokens, API keys, sensitive URL parameters, and token-shaped strings are redacted. Generated directories, dependencies, and paths outside the repository are rejected as related code locations.

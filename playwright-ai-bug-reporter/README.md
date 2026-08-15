# Playwright AI Bug Reporter

A QA automation project that uses Playwright and AI to transform failed end-to-end tests into structured bug reports.

## Project Goal

The project will:

1. Run Playwright end-to-end tests.
2. Collect evidence when a test fails.
3. Send structured failure evidence to an AI model.
4. Generate a professional bug report.
5. Save the report locally as a Markdown or JSON file.

## Project Structure

- `src/ai` — AI bug-report generation
- `src/reporters` — Playwright reporter integration
- `src/types` — TypeScript data structures
- `src/utils` — failure-evidence preparation
- `tests` — Playwright end-to-end tests
- `bug-reports` — generated bug reports
- `.env.example` — required environment-variable names
- `playwright.config.ts` — Playwright configuration
- `tsconfig.json` — TypeScript configuration

## Install Dependencies

```powershell
npm.cmd install
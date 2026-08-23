## Playwright Bug Report Assistant

An automated Playwright reporter written in TypeScript that captures failed-test details and saves structured bug reports for human review.

When a Playwright test fails unexpectedly, the reporter collects the error, stack trace, test steps, environment information, and available evidence such as screenshots, videos, and traces. It then writes a report to test-results/bug-reports.

The current version generates deterministic reports from Playwright test data. It does not yet call an AI model or API.

### Features

Runs automatically after an unexpected Playwright test failure
Captures the test title, file location, status, duration, retry number, and timestamps
Records the error message and stack trace
Collects Playwright test steps
Records the operating system, Playwright project, and browser
Finds screenshots, videos, traces, and other attachments
Supports Markdown, JSON, and plain-text formatting
Creates safe, unique filenames
Creates missing output directories automatically
Leaves Human Review fields for defect confirmation, severity, priority, final title, notes, and ticket URL

### Requirements

Node.js
npm
Playwright Test
TypeScript
The project was developed with Node.js 24 and Playwright using TypeScript.
Installation
Open a terminal in the project directory:
cd C:\Users\benja\OneDrive\Documents\GitHub\python_projects\playwright-bug-report-assistant

### Install the project dependencies:
npm.cmd install
Install the Playwright browsers if they are not already installed:
npx.cmd playwright install
npx.cmd is used in these Windows PowerShell examples because some systems block the npx.ps1 script through their execution policy.

### Verify the TypeScript Code
Check the project without creating compiled output files:

npx.cmd tsc --noEmit
No terminal output means the TypeScript check passed.

### Run the Tests
npx.cmd playwright test
Passing tests do not generate bug reports. An unexpected failed test triggers the custom reporter automatically.

### Report Location
Generated reports are saved in:

test-results/
└── bug-reports/
    └── generated-report-name.md

To open the report directory in Windows File Explorer:
explorer.exe .\test-results\bug-reports
If retries are enabled, the reporter creates a separate report for each failed attempt. This preserves the evidence and timing information from every attempt.

### Example Passing Test

import {
  test,
  expect,
} from "@playwright/test";

test(
  "displays the sample page",
  async ({ page }) => {
    await page.setContent(
      "<h1>Bug Report Assistant</h1>"
    );

    await expect(
      page.getByRole("heading", {
        name: "Bug Report Assistant",
      })
    ).toBeVisible();
  }
);

This test should pass and should not create a report. In normal use, reports are created when an application defect causes a real test expectation to fail.

### Report Contents

A Markdown report includes:
Test Summary
Failure Details
Stack Trace
Test Steps
Environment
Evidence

Screenshots

Traces

Videos

Other Attachments

Human Review
The Human Review section initially contains pending values so a person can confirm the defect and complete its severity, priority, final title, notes, and ticket URL.

### Project Structure

playwright-bug-report-assistant/
├── src/
│   ├── bug-report-generator.ts
│   ├── bug-report-reporter.ts
│   ├── file-utils.ts
│   ├── text-utils.ts
│   └── types.ts
├── tests/
│   └── bug-report-assistant.spec.ts
├── playwright.config.ts
├── package.json
└── README.md

### Main Files

src/bug-report-generator.ts collects failure data, normalizes it, formats reports, and coordinates saving.
src/bug-report-reporter.ts connects the report workflow to Playwright's onTestEnd() reporter event.
src/file-utils.ts creates safe filenames, creates output directories, and writes report files.
src/text-utils.ts cleans error text, escapes Markdown, and provides text-related helpers.
src/types.ts defines the shared TypeScript data structures.

### Reporter Configuration

The custom reporter is registered in playwright.config.ts:

reporter: [
  ["list"],
  ["./src/bug-report-reporter.ts"],
],

The list reporter continues to show test results in the terminal, while the custom reporter saves bug reports for unexpected failures.
Output Formats
The generator supports:
markdown → .md
json → .json
plain_text → .txt
The custom Playwright reporter currently requests Markdown output.

### View a Playwright Trace

When a failed test includes a trace, Playwright prints a command similar to:
npx.cmd playwright show-trace path\to\trace.zip
Run the exact command printed by Playwright to inspect the recorded test execution.

### Troubleshooting
PowerShell blocks npx
Use npx.cmd instead:
npx.cmd playwright test

### Python reports a syntax error on a TypeScript import

Do not run .ts files with the Python Run button. Use the TypeScript compiler or Playwright commands from the terminal:
npx.cmd tsc --noEmit
npx.cmd playwright test

### No report appears

Confirm that:
The test failed unexpectedly.
The custom reporter is registered in playwright.config.ts.
The terminal printed Bug report saved: followed by a path.
You are looking inside test-results/bug-reports.

### Multiple reports appear

Playwright retries can produce multiple failed attempts. The reporter intentionally saves one report for each failed attempt.

### Current Status
The project successfully:
Passes TypeScript validation
Runs Playwright tests
Detects unexpected failures
Captures Playwright evidence
Creates missing report directories
Saves Markdown bug reports automatically

### Possible Future Enhancements

Optional AI-assisted failure summaries and investigation suggestions
Report only the final failed retry
Configurable output format and output directory
Links to issue trackers
Automated unit tests for report formatting and evidence classification

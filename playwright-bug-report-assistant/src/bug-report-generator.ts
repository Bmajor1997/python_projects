import { existsSync } from "node:fs";
import { platform, release } from "node:os";
import { join } from "node:path";
import type { TestResult } from "@playwright/test/reporter";
import { make_filename, save_file } from "./file-utils";
import {
  clean_error_text,
  escape_markdown,
  log_error
} from "./text-utils";
import type {
  BugReportData,
  EnvironmentDetails,
  EvidenceFiles,
  FailedTest,
  FailureDetails,
  HumanReview
} from "./types";

// Returns the useful Playwright test steps in their execution order.
export function get_test_steps(result: TestResult): string[] {
    const step_titles: string[] = [];
    const pending_steps = [...result.steps];
    while (pending_steps.length > 0) {
  const current_step = pending_steps.shift();

  if (!current_step) {
    continue;

  }

  if (current_step.category === "test.step") {
  step_titles.push(current_step.title);
}

pending_steps.unshift(...current_step.steps);
}

    return step_titles;
}

// Collects the test, error, timing, retry, and step details for one failure.
export function collect_failure_details(
  failure: FailedTest
): FailureDetails {
    const { test, result } = failure;
    const primary_error = result.errors[0];

    const error_message = clean_error_text(
        primary_error?.message ?? "The test failed without an error message."
);

    const stack_trace = primary_error?.stack
        ? clean_error_text(primary_error.stack)
        : null;

    const test_steps = get_test_steps(result);

    return {
        testTitle: test.titlePath().join(" > "),
        testFile: test.location.file,
        lineNumber: test.location.line,
        columnNumber: test.location.column,
        status: result.status,
        errorMessage: error_message,
        stackTrace: stack_trace,
        startTime: result.startTime,
        durationMs: result.duration,
        retryNumber: result.retry,
        testSteps: test_steps,
        };
      }
    // Finds the screenshots, traces, videos, and other attachments available for a failed test.
export function find_evidence(result: TestResult): EvidenceFiles {
    const screenshot_paths: string[] = [];
    const trace_paths: string[] = [];
    const video_paths: string[] = [];
    const other_attachments: string[] = [];

   for (const attachment of result.attachments) {
  if (!attachment.path || !existsSync(attachment.path)) {
    continue;
  }

  const attachment_name = attachment.name.toLowerCase();
  const content_type = attachment.contentType.toLowerCase();

  if (
    content_type.startsWith("image/") ||
    attachment_name.includes("screenshot")
  ) {
    screenshot_paths.push(attachment.path);
    continue;
  }

  if (attachment_name.includes("trace")) {
    trace_paths.push(attachment.path);
    continue;
  }

  if (
    content_type.startsWith("video/") ||
    attachment_name.includes("video")
  ) {
    video_paths.push(attachment.path);
    continue;
  }

  other_attachments.push(attachment.path);

  return {
    screenshotPaths: screenshot_paths,
    tracePaths: trace_paths,
    videoPaths: video_paths,
    otherAttachments: other_attachments,
  };
  }
}
  
// Collects the available operating system, browser, project, and execution details.
export function collect_environment(
  failure: FailedTest
): EnvironmentDetails {
  const { test, result } = failure;
  const raw_operating_system = platform();
  const system_release = release();

  let operating_system: string;

  if (raw_operating_system === "win32") {
    operating_system = "Windows";
  } else if (raw_operating_system === "darwin") {
    operating_system = "macOS";
  } else if (raw_operating_system === "linux") {
    operating_system = "Linux";
  } else {
    operating_system = raw_operating_system;
  }

  const project = test.parent.project();
  let project_name: string;

  if (project?.name) {
    project_name = project.name;
  } else {
    project_name = "Unknown";
  }

  const browser = project?.use.browserName;
  let browser_name: string;

  if (browser) {
    browser_name = browser;
  } else {
    browser_name = "Unknown";
  }

  const execution_time = result.startTime;

  return {
    operatingSystem: operating_system,
    systemRelease: system_release,
    projectName: project_name,
    browserName: browser_name,
    executionTime: execution_time,
  };
}

const automated_warning =  "This report was generated automatically and requires human review.";
  
export function build_report_data(
  details:FailureDetails,
  evidence: EvidenceFiles,
  environment: EnvironmentDetails,
   
): BugReportData {
    const human_review: HumanReview = {
      confirmedDefect: null,
      severity: null,
      priority: null,
      finalTitle: null,
      notes: null,
      ticketUrl: null,
};
    const generated_at = new Date();

    return {
      details,
      evidence,
      environment,
      humanReview: human_review,
      generatedAt: generated_at,
      automatedWarning: automated_warning,
    };
}
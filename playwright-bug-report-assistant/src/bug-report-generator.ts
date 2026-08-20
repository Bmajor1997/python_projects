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
    
export function find_evidence(
  result: TestResult
): EvidenceFiles {
  const screenshot_paths: string[] = [];
  const trace_paths: string[] = [];
  const video_paths: string[] = [];
  const other_attachments: string[] = [];

  for (const attachment of result.attachments) {
    if (
      !attachment.path ||
      !existsSync(attachment.path)
    ) {
      continue;
    }

    const attachment_name =
      attachment.name.toLowerCase();

    const content_type =
      attachment.contentType.toLowerCase();

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
  }

  return {
    screenshotPaths: screenshot_paths,
    tracePaths: trace_paths,
    videoPaths: video_paths,
    otherAttachments: other_attachments,
  };
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

export function normalize_report_data(
  report_data: BugReportData
): BugReportData {
  const {
    details,
    evidence,
    environment,
    humanReview: human_review,
    generatedAt: generated_at,
    automatedWarning: automated_warning,
  } = report_data;

  const normalized_test_steps =
    details.testSteps
      .map((step) => step.trim())
      .filter((step) => step.length > 0);

  const normalized_details: FailureDetails = {
    ...details,
    testTitle: details.testTitle.trim(),
    testFile: details.testFile.trim(),
    errorMessage: details.errorMessage.trim(),
    stackTrace: details.stackTrace
      ? details.stackTrace.trim()
      : details.stackTrace,
    testSteps: normalized_test_steps,
  };

  const normalized_evidence: EvidenceFiles = {
    screenshotPaths: evidence.screenshotPaths
      .map((path) => path.trim())
      .filter((path) => path.length > 0),

    tracePaths: evidence.tracePaths
      .map((path) => path.trim())
      .filter((path) => path.length > 0),

    videoPaths: evidence.videoPaths
      .map((path) => path.trim())
      .filter((path) => path.length > 0),

    otherAttachments: evidence.otherAttachments
      .map((path) => path.trim())
      .filter((path) => path.length > 0),
  };

  const normalized_environment: EnvironmentDetails = {
    ...environment,
    operatingSystem:
      environment.operatingSystem.trim(),
    systemRelease:
      environment.systemRelease.trim(),
    projectName:
      environment.projectName.trim(),
    browserName:
      environment.browserName.trim(),
  };

  const normalized_human_review: HumanReview = {
    confirmedDefect:
      human_review.confirmedDefect?.trim() || null,

    severity:
      human_review.severity?.trim() || null,

    priority:
      human_review.priority?.trim() || null,

    finalTitle:
      human_review.finalTitle?.trim() || null,

    notes:
      human_review.notes?.trim() || null,

    ticketUrl:
      human_review.ticketUrl?.trim() || null,
  };

  return {
    details: normalized_details,
    evidence: normalized_evidence,
    environment: normalized_environment,
    humanReview: normalized_human_review,
    generatedAt: generated_at,
    automatedWarning: automated_warning.trim(),
  };
}

export function format_markdown(
  report_data: BugReportData
): string {
  const {
    details,
    evidence,
    environment,
    humanReview: human_review,
    generatedAt: generated_at,
    automatedWarning: automated_warning,
  } = report_data;

  const duration_seconds =
    (details.durationMs / 1000).toFixed(2);

  const test_location =
    `${details.testFile}:${details.lineNumber}:${details.columnNumber}`;

  const formatted_start_time =
    details.startTime.toISOString();

  const formatted_execution_time =
    environment.executionTime.toISOString();

  const formatted_generated_at =
    generated_at.toISOString();

  const markdown_lines: string[] = [];

  markdown_lines.push(
    `# Bug Report: ${escape_markdown(details.testTitle)}`
  );

  markdown_lines.push("");

  markdown_lines.push(
    `> ${escape_markdown(automated_warning)}`
  );

  markdown_lines.push("");
  markdown_lines.push("## Test Summary");
  markdown_lines.push("");
  markdown_lines.push("| Field | Value |");
  markdown_lines.push("| --- | --- |");

  markdown_lines.push(
    `| Test Title | ${escape_markdown(details.testTitle)} |`
  );

  markdown_lines.push(
    `| Status | ${escape_markdown(details.status)} |`
  );

  markdown_lines.push(
    `| Location | ${escape_markdown(test_location)} |`
  );

  markdown_lines.push(
    `| Start Time | ${escape_markdown(formatted_start_time)} |`
  );

  markdown_lines.push(
    `| Duration | ${escape_markdown(duration_seconds)} seconds |`
  );

  markdown_lines.push(
    `| Retry Number | ${details.retryNumber} |`
  );

  markdown_lines.push("");
  markdown_lines.push("## Failure Details");
  markdown_lines.push("");
  markdown_lines.push("```text");
  markdown_lines.push(details.errorMessage);
  markdown_lines.push("```");

  markdown_lines.push("");
  markdown_lines.push("## Stack Trace");
  markdown_lines.push("");
  markdown_lines.push("```text");

  if (details.stackTrace) {
    markdown_lines.push(details.stackTrace);
  } else {
    markdown_lines.push("Not available");
  }

  markdown_lines.push("```");

  markdown_lines.push("");
  markdown_lines.push("## Test Steps");
  markdown_lines.push("");

  if (details.testSteps.length === 0) {
    markdown_lines.push("No test steps recorded");
  } else {
    let step_number = 1;

    for (const step of details.testSteps) {
      markdown_lines.push(
        `${step_number}. ${escape_markdown(step)}`
      );

      step_number++;
    }
  }

  markdown_lines.push("");
  markdown_lines.push("## Environment");
  markdown_lines.push("");
  markdown_lines.push("| Field | Value |");
  markdown_lines.push("| --- | --- |");

  markdown_lines.push(
    `| Operating System | ${escape_markdown(environment.operatingSystem)} |`
  );

  markdown_lines.push(
    `| System Release | ${escape_markdown(environment.systemRelease)} |`
  );

  markdown_lines.push(
    `| Project Name | ${escape_markdown(environment.projectName)} |`
  );

  markdown_lines.push(
    `| Browser Name | ${escape_markdown(environment.browserName)} |`
  );

  markdown_lines.push(
    `| Execution Time | ${escape_markdown(formatted_execution_time)} |`
  );

  markdown_lines.push(
    `| Report Generated At | ${escape_markdown(formatted_generated_at)} |`
  );

  markdown_lines.push("");
  markdown_lines.push("## Evidence");
  markdown_lines.push("");

  markdown_lines.push("### Screenshots");
  markdown_lines.push("");

  if (evidence.screenshotPaths.length === 0) {
    markdown_lines.push("No screenshots captured");
  } else {
    for (const screenshot_path of evidence.screenshotPaths) {
      markdown_lines.push(
        `- \`${escape_markdown(screenshot_path)}\``
      );
    }
  }

  markdown_lines.push("");
  markdown_lines.push("### Traces");
  markdown_lines.push("");

  if (evidence.tracePaths.length === 0) {
    markdown_lines.push("No trace captured");
  } else {
    for (const trace_path of evidence.tracePaths) {
      markdown_lines.push(
        `- \`${escape_markdown(trace_path)}\``
      );
    }
  }

  markdown_lines.push("");
  markdown_lines.push("### Videos");
  markdown_lines.push("");

  if (evidence.videoPaths.length === 0) {
    markdown_lines.push("No videos captured");
  } else {
    for (const video_path of evidence.videoPaths) {
      markdown_lines.push(
        `- \`${escape_markdown(video_path)}\``
      );
    }
  }

  markdown_lines.push("");
  markdown_lines.push("### Other Attachments");
  markdown_lines.push("");

  if (evidence.otherAttachments.length === 0) {
    markdown_lines.push("No other attachments captured");
  } else {
    for (
      const other_attachment
      of evidence.otherAttachments
    ) {
      markdown_lines.push(
        `- \`${escape_markdown(other_attachment)}\``
      );
    }
  }

  markdown_lines.push("");
  markdown_lines.push("## Human Review");
  markdown_lines.push("");
  markdown_lines.push("| Field | Value |");
  markdown_lines.push("| --- | --- |");

  let confirmed_defect_value: string;

  if (human_review.confirmedDefect) {
    confirmed_defect_value = human_review.confirmedDefect;
  } else {
    confirmed_defect_value = "Pending";
  }

  markdown_lines.push(
    `| Confirmed Defect | ${confirmed_defect_value} |`
  );

  let severity_value: string;

  if (human_review.severity) {
    severity_value = human_review.severity;
  } else {
    severity_value = "Pending review";
  }

  markdown_lines.push(
    `| Severity | ${escape_markdown(severity_value)} |`
  );

  let priority_value: string;

  if (human_review.priority) {
    priority_value = human_review.priority;
  } else {
    priority_value = "Pending review";
  }

  markdown_lines.push(
    `| Priority | ${escape_markdown(priority_value)} |`
  );

  let final_title_value: string;

  if (human_review.finalTitle) {
    final_title_value = human_review.finalTitle;
  } else {
    final_title_value = "Pending review";
  }

  markdown_lines.push(
    `| Final Title | ${escape_markdown(final_title_value)} |`
  );

  let notes_value: string;

  if (human_review.notes) {
    notes_value = human_review.notes;
  } else {
    notes_value = "Pending";
  }

  markdown_lines.push(
    `| Notes | ${escape_markdown(notes_value)} |`
  );

  let ticket_url_value: string;

  if (human_review.ticketUrl) {
    ticket_url_value = human_review.ticketUrl;
  } else {
    ticket_url_value = "Pending";
  }

  markdown_lines.push(
    `| Ticket URL | ${escape_markdown(ticket_url_value)} |`
  );

  return markdown_lines.join("\n");
}

export function format_json(
  report_data: BugReportData
): string {
    const formatted_json =
      JSON.stringify(report_data, null, 2);

      return formatted_json;
}

export function format_plain_text(
  report_data: BugReportData
): string {
  const {
    details,
    evidence,
    environment,
    humanReview: human_review,
    generatedAt: generated_at,
    automatedWarning: automated_warning,
  } = report_data;

  const duration_seconds =
    (details.durationMs / 1000).toFixed(2);

  const test_location =
    `${details.testFile}:${details.lineNumber}:${details.columnNumber}`;

  const formatted_start_time =
    details.startTime.toISOString();

  const formatted_execution_time =
    environment.executionTime.toISOString();

  const formatted_generated_at =
    generated_at.toISOString();

  const text_lines: string[] = [];

  text_lines.push(
    `BUG REPORT: ${details.testTitle}`
  );

  text_lines.push("");
  text_lines.push(automated_warning);
  text_lines.push("");

  text_lines.push("TEST SUMMARY");
  text_lines.push("--------------------");

  text_lines.push(
    `Test Title: ${details.testTitle}`
  );

  text_lines.push(
    `Status: ${details.status}`
  );

  text_lines.push(
    `Location: ${test_location}`
  );

  text_lines.push(
    `Start Time: ${formatted_start_time}`
  );

  text_lines.push(
    `Duration: ${duration_seconds} seconds`
  );

  text_lines.push(
    `Retry Number: ${details.retryNumber}`
  );

  text_lines.push("");

  text_lines.push("FAILURE DETAILS");
  text_lines.push("--------------------");
  text_lines.push(details.errorMessage);
  text_lines.push("");

  text_lines.push("STACK TRACE");
  text_lines.push("--------------------");

  if (details.stackTrace) {
    text_lines.push(details.stackTrace);
  } else {
    text_lines.push("Not available");
  }

  text_lines.push("");

  text_lines.push("TEST STEPS");
  text_lines.push("--------------------");

  if (details.testSteps.length === 0) {
    text_lines.push("No test steps recorded");
  } else {
    let step_number = 1;

    for (const step of details.testSteps) {
      text_lines.push(
        `${step_number}. ${step}`
      );

      step_number++;
    }
  }

  text_lines.push("");

  text_lines.push("ENVIRONMENT");
  text_lines.push("--------------------");

  text_lines.push(
    `Operating System: ${environment.operatingSystem}`
  );

  text_lines.push(
    `System Release: ${environment.systemRelease}`
  );

  text_lines.push(
    `Project Name: ${environment.projectName}`
  );

  text_lines.push(
    `Browser Name: ${environment.browserName}`
  );

  text_lines.push(
    `Execution Time: ${formatted_execution_time}`
  );

  text_lines.push(
    `Report Generated At: ${formatted_generated_at}`
  );

  text_lines.push("");

  text_lines.push("EVIDENCE");
  text_lines.push("--------------------");

  text_lines.push("Screenshots:");

  if (evidence.screenshotPaths.length === 0) {
    text_lines.push("No screenshots captured");
  } else {
    for (
      const screenshot_path
      of evidence.screenshotPaths
    ) {
      text_lines.push(
        `- ${screenshot_path}`
      );
    }
  }

  text_lines.push("");

  text_lines.push("Traces:");

  if (evidence.tracePaths.length === 0) {
    text_lines.push("No traces captured");
  } else {
    for (const trace_path of evidence.tracePaths) {
      text_lines.push(
        `- ${trace_path}`
      );
    }
  }

  text_lines.push("");

  text_lines.push("Videos:");

  if (evidence.videoPaths.length === 0) {
    text_lines.push("No videos captured");
  } else {
    for (const video_path of evidence.videoPaths) {
      text_lines.push(
        `- ${video_path}`
      );
    }
  }

  text_lines.push("");

  text_lines.push("Other Attachments:");

  if (evidence.otherAttachments.length === 0) {
    text_lines.push(
      "No other attachments captured"
    );
  } else {
    for (
      const other_attachment
      of evidence.otherAttachments
    ) {
      text_lines.push(
        `- ${other_attachment}`
      );
    }
  }

  text_lines.push("");

  text_lines.push("HUMAN REVIEW");
  text_lines.push("--------------------");

  let confirmed_defect_value: string;

  if (human_review.confirmedDefect) {
    confirmed_defect_value =
      human_review.confirmedDefect;
  } else {
    confirmed_defect_value = "Pending review";
  }

  text_lines.push(
    `Confirmed Defect: ${confirmed_defect_value}`
  );

  let severity_value: string;

  if (human_review.severity) {
    severity_value = human_review.severity;
  } else {
    severity_value = "Pending review";
  }

  text_lines.push(
    `Severity: ${severity_value}`
  );

  let priority_value: string;

  if (human_review.priority) {
    priority_value = human_review.priority;
  } else {
    priority_value = "Pending review";
  }

  text_lines.push(
    `Priority: ${priority_value}`
  );

  let final_title_value: string;

  if (human_review.finalTitle) {
    final_title_value = human_review.finalTitle;
  } else {
    final_title_value = "Pending review";
  }

  text_lines.push(
    `Final Title: ${final_title_value}`
  );

  let notes_value: string;

  if (human_review.notes) {
    notes_value = human_review.notes;
  } else {
    notes_value = "Pending";
  }

  text_lines.push(
    `Notes: ${notes_value}`
  );

  let ticket_url_value: string;

  if (human_review.ticketUrl) {
    ticket_url_value = human_review.ticketUrl;
  } else {
    ticket_url_value = "Pending";
  }

  text_lines.push(
    `Ticket URL: ${ticket_url_value}`
  );

  return text_lines.join("\n");
}

export function generate_bug_report(
  report_data: BugReportData,
  output_format: "markdown" | "json" | "plain_text"
): string{

    const normalized_report_data =
      normalize_report_data(report_data);

    if (output_format === "markdown"){
        return format_markdown(normalized_report_data);
    }

    else if (output_format === "json"){
      return format_json(normalized_report_data);
    }
    else if (output_format === "plain_text") {
      return format_plain_text(normalized_report_data);
    }
    else{
      throw new Error(
        `Unsupported report format: ${output_format}`
      )
    }
  }

export async function save_bug_report(
  failure: FailedTest,
  output_directory: string,
  output_format: "markdown" | "json" | "plain_text"
): Promise<string> {
  const details =
    collect_failure_details(failure);

  const evidence =
    find_evidence(failure.result);

  const environment =
    collect_environment(failure);

  const report_data =
    build_report_data(
      details,
      evidence,
      environment
    );

  const report_contents =
    generate_bug_report(
      report_data,
      output_format
    );

  const markdown_filename =
    make_filename(report_data);

  let output_extension: string;

  if (output_format === "markdown") {
    output_extension = ".md";
  } else if (output_format === "json") {
    output_extension = ".json";
  } else {
    output_extension = ".txt";
  }

  const output_filename =
    markdown_filename.replace(
      /\.md$/,
      output_extension
    );

  const output_path =
    join(output_directory, output_filename);

  await save_file(
    output_path,
    report_contents
  );

  return output_path;
}
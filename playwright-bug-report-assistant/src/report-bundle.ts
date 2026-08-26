import { copyFile, mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import { basename, join, relative } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";
import { format_html } from "./html-report";
import { format_markdown, normalize_report_data } from "./bug-report-generator";
import { make_report_folder_name } from "./file-utils";
import type { BugReportData, GeneratedReports, ReportFormatOptions } from "./types";
import { create_docx_report } from "./docx-report";

export const DEFAULT_REPORT_FORMATS: ReportFormatOptions = { markdown: true, html: true, pdf: true, docx: true };
export type PdfWriter = (htmlPath: string, pdfPath: string) => Promise<void>;
export type DocxWriter = (data: BugReportData, docxPath: string) => Promise<void>;

export function boolean_setting(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined || value === "") return fallback;
  if (/^(1|true|yes|on)$/i.test(value)) return true;
  if (/^(0|false|no|off)$/i.test(value)) return false;
  throw new Error(`Expected a boolean setting, received: ${value}`);
}
export function report_formats_from_env(env: NodeJS.ProcessEnv = process.env): ReportFormatOptions {
  return { markdown: boolean_setting(env.BUG_REPORT_MARKDOWN, true), html: boolean_setting(env.BUG_REPORT_HTML, true), pdf: boolean_setting(env.BUG_REPORT_PDF, true), docx: boolean_setting(env.BUG_REPORT_DOCX, true) };
}
export const write_pdf: PdfWriter = async (htmlPath, pdfPath) => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.pdf({ path: pdfPath, format: "A4", printBackground: true, displayHeaderFooter: true,
      margin: { top: "20mm", right: "14mm", bottom: "19mm", left: "14mm" },
      headerTemplate: '<div style="font:9px Arial;color:#667085;width:100%;padding:0 14mm">Playwright Bug Report</div>',
      footerTemplate: '<div style="font:9px Arial;color:#667085;width:100%;padding:0 14mm;display:flex;justify-content:space-between"><span>Automatically generated - human review required</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>' });
  } finally { await browser.close(); }
};

async function localize_evidence(data: BugReportData, directory: string): Promise<{ data: BugReportData; screenshotSource?: string }> {
  const evidenceDirectory = join(directory, "evidence");
  await mkdir(evidenceDirectory, { recursive: true });
  const used = new Map<string, number>();
  const copy = async (source: string): Promise<string> => {
    const original = basename(source) || "attachment";
    const count = used.get(original) ?? 0; used.set(original, count + 1);
    const dot = original.lastIndexOf(".");
    const name = count === 0 ? original : dot > 0 ? `${original.slice(0, dot)}-${count + 1}${original.slice(dot)}` : `${original}-${count + 1}`;
    const destination = join(evidenceDirectory, name);
    try { await copyFile(source, destination); return relative(directory, destination).replace(/\\/g, "/"); }
    catch { return source.replace(/\\/g, "/"); }
  };
  const localized = structuredClone(data);
  localized.evidence.screenshotPaths = await Promise.all(data.evidence.screenshotPaths.map(copy));
  localized.evidence.tracePaths = await Promise.all(data.evidence.tracePaths.map(copy));
  localized.evidence.otherAttachments = await Promise.all(data.evidence.otherAttachments.map(copy));
  let screenshotSource: string | undefined;
  if (localized.evidence.screenshotPaths[0]?.startsWith("evidence/")) {
    try {
      const path = join(directory, localized.evidence.screenshotPaths[0]);
      const extension = path.toLowerCase().split(".").at(-1);
      const mime = extension === "jpg" || extension === "jpeg" ? "image/jpeg" : extension === "webp" ? "image/webp" : "image/png";
      screenshotSource = `data:${mime};base64,${(await readFile(path)).toString("base64")}`;
    } catch { /* the evidence link remains available */ }
  }
  return { data: localized, screenshotSource };
}

async function screenshot_source(data: BugReportData, directory: string): Promise<string | undefined> {
  const first = data.evidence.screenshotPaths[0];
  if (!first) return undefined;
  try {
    const path = join(directory, first);
    const extension = path.toLowerCase().split(".").at(-1);
    const mime = extension === "jpg" || extension === "jpeg" ? "image/jpeg" : extension === "webp" ? "image/webp" : "image/png";
    return `data:${mime};base64,${(await readFile(path)).toString("base64")}`;
  } catch { return undefined; }
}

export function serialize_report_data(input: BugReportData): string {
  return JSON.stringify(normalize_report_data(input), null, 2);
}

export async function read_report_data(path: string): Promise<BugReportData> {
  const parsed = JSON.parse(await readFile(path, "utf8")) as BugReportData;
  parsed.details.startTime = new Date(parsed.details.startTime);
  parsed.environment.executionTime = new Date(parsed.environment.executionTime);
  parsed.generatedAt = new Date(parsed.generatedAt);
  return normalize_report_data(parsed);
}

async function write_report_files(data: BugReportData, directory: string, formats: ReportFormatOptions, pdfWriter: PdfWriter, docxWriter: DocxWriter, screenshotSource?: string): Promise<GeneratedReports> {
  const reports: GeneratedReports = { directory, data: join(directory, "bug-report-data.json") };
  await writeFile(reports.data, serialize_report_data(data), "utf8");
  if (formats.markdown) { reports.markdown = join(directory, "bug-report.md"); await writeFile(reports.markdown, format_markdown(data), "utf8"); }
  if (formats.docx) {
    reports.docx = join(directory, "bug-report.docx");
    try { await docxWriter(data, reports.docx); }
    catch (error) { reports.docx = undefined; reports.docxError = error instanceof Error ? error.message : String(error); }
  }
  if (formats.html || formats.pdf) { reports.html = join(directory, "bug-report.html"); await writeFile(reports.html, format_html(data, screenshotSource), "utf8"); }
  if (formats.pdf) {
    reports.pdf = join(directory, "bug-report.pdf");
    try { await pdfWriter(reports.html!, reports.pdf); }
    catch (error) { reports.pdf = undefined; reports.pdfError = error instanceof Error ? error.message : String(error); }
  }
  if (!formats.html && reports.pdf) { await unlink(reports.html!); reports.html = undefined; }
  return reports;
}

export async function save_report_bundle(input: BugReportData, outputRoot: string, formats: ReportFormatOptions = DEFAULT_REPORT_FORMATS, pdfWriter: PdfWriter = write_pdf, docxWriter: DocxWriter = create_docx_report): Promise<GeneratedReports> {
  const sanitized = normalize_report_data(input);
  const directory = join(outputRoot, make_report_folder_name(sanitized));
  await mkdir(directory, { recursive: true });
  const localized = await localize_evidence(sanitized, directory), data = localized.data;
  return write_report_files(data, directory, formats, pdfWriter, docxWriter, localized.screenshotSource);
}

export async function regenerate_report_bundle(input: BugReportData, directory: string, formats: ReportFormatOptions = DEFAULT_REPORT_FORMATS, pdfWriter: PdfWriter = write_pdf, docxWriter: DocxWriter = create_docx_report): Promise<GeneratedReports> {
  const data = normalize_report_data(input);
  await mkdir(directory, { recursive: true });
  return write_report_files(data, directory, formats, pdfWriter, docxWriter, await screenshot_source(data, directory));
}

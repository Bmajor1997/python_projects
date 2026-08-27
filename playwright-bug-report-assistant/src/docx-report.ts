import { readFile, writeFile } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, Footer, Header, HeadingLevel, ImageRun,
  LevelFormat, Packer, PageNumber, Paragraph, Table, TableCell, TableLayoutType, TableRow,
  TextRun, VerticalAlign, WidthType,
} from "docx";
import { normalize_report_data } from "./bug-report-generator";
import { categorize_failure } from "./fingerprint";
import { friendly_report_title, friendly_test_name } from "./text-utils";
import type { FailureAnalysisData } from "./types";

const BLUE = "2E74B5", DARK_BLUE = "1F4D78", INK = "172033", MUTED = "667085", FILL = "E8EEF5", LINE = "D7DCE5";
const TABLE_WIDTH = 9360, TABLE_INDENT = 120, CELL_MARGINS = { top: 80, bottom: 80, left: 120, right: 120 };
const show = (value: unknown) => value === null || value === undefined || value === "" ? "Unavailable" : String(value);

function heading(text: string, level: typeof HeadingLevel.HEADING_1 | typeof HeadingLevel.HEADING_2): Paragraph {
  return new Paragraph({ text, heading: level, keepNext: true });
}
function labelValueRows(items: Array<[string, unknown]>): Table {
  return new Table({ width: { size: TABLE_WIDTH, type: WidthType.DXA }, indent: { size: TABLE_INDENT, type: WidthType.DXA }, layout: TableLayoutType.FIXED,
    columnWidths: [2700, 6660], margins: CELL_MARGINS,
    borders: { top: { style: BorderStyle.SINGLE, size: 1, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 1, color: LINE }, left: { style: BorderStyle.SINGLE, size: 1, color: LINE }, right: { style: BorderStyle.SINGLE, size: 1, color: LINE }, insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: LINE }, insideVertical: { style: BorderStyle.SINGLE, size: 1, color: LINE } },
    rows: items.map(([label, value]) => new TableRow({ cantSplit: true, children: [
      new TableCell({ width: { size: 2700, type: WidthType.DXA }, shading: { fill: FILL }, verticalAlign: VerticalAlign.CENTER, margins: CELL_MARGINS, children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, color: DARK_BLUE })] })] }),
      new TableCell({ width: { size: 6660, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, margins: CELL_MARGINS, children: [new Paragraph({ text: show(value) })] }),
    ] })) });
}
function bullet(text: string): Paragraph { return new Paragraph({ text, numbering: { reference: "report-bullets", level: 0 } }); }
function numbered(text: string): Paragraph { return new Paragraph({ text, numbering: { reference: "report-steps", level: 0 } }); }
function evidenceParagraph(path: string): Paragraph {
  return new Paragraph({ children: [new ExternalHyperlink({ link: path.replace(/\\/g, "/"), children: [new TextRun({ text: path, color: BLUE, underline: {} })] })] });
}
function imageSize(data: Buffer): { width: number; height: number } {
  let width = 1280, height = 720;
  if (data.length >= 24 && data.subarray(1, 4).toString() === "PNG") { width = data.readUInt32BE(16); height = data.readUInt32BE(20); }
  const maxWidth = 560, maxHeight = 420, scale = Math.min(maxWidth / width, maxHeight / height, 1);
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}
async function screenshotParagraph(data: FailureAnalysisData, outputPath: string): Promise<Paragraph> {
  const relativePath = data.evidence.screenshotPaths[0];
  if (!relativePath) return new Paragraph({ text: "No screenshot captured." });
  try {
    const path = join(dirname(outputPath), relativePath), bytes = await readFile(path), extension = extname(path).toLowerCase();
    const type = extension === ".jpg" || extension === ".jpeg" ? "jpg" : extension === ".gif" ? "gif" : extension === ".bmp" ? "bmp" : "png";
    return new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type, data: bytes, transformation: imageSize(bytes), altText: { title: "Failure screenshot", description: "Screenshot captured when the Playwright test failed", name: "Failure screenshot" } })] });
  } catch { return new Paragraph({ text: `Screenshot available separately: ${relativePath}` }); }
}

export async function create_docx_report(input: FailureAnalysisData, outputPath: string): Promise<void> {
  const data = normalize_report_data(input), { details: d, evidence: e, environment: n } = data;
  const title = data.aiAnalysis?.title ?? friendly_report_title(d.errorMessage, d.testTitle, d.expectedBehavior, d.actualBehavior);
  const children: Array<Paragraph | Table> = [
    new Paragraph({ children: [new TextRun({ text: title, bold: true, size: 44, color: INK })], spacing: { after: 160 }, keepNext: true }),
    new Paragraph({ children: [new TextRun({ text: data.automatedWarning, italics: true, color: MUTED })], spacing: { after: 180 } }),
    heading("Summary", HeadingLevel.HEADING_1),
    labelValueRows([["Status", d.status], ["Failure category", categorize_failure(d.errorMessage)], ["Fingerprint", data.fingerprint], ["Stability", `${data.stability.classification} (${data.stability.sampleSize} samples)`], ["What went wrong", d.errorMessage]]),
    heading("Reproduction", HeadingLevel.HEADING_1),
    labelValueRows([["Test", friendly_test_name(d.testTitle)], ["Failed step", d.failedStep], ["Expected", d.expectedBehavior], ["Actual", d.actualBehavior], ["URL", e.currentUrl], ["Retry", d.retryNumber]]),
    heading("Steps", HeadingLevel.HEADING_2),
    ...(d.testSteps.length ? d.testSteps.map(numbered) : [new Paragraph({ text: "Unavailable" })]),
    heading("Environment and CI", HeadingLevel.HEADING_1),
    labelValueRows([["Browser / project", `${n.browserName} / ${n.projectName}`], ["OS", `${n.operatingSystem} ${n.systemRelease}`], ["Viewport", n.viewport ? `${n.viewport.width} x ${n.viewport.height}` : null], ["Locale / timezone", `${show(n.locale)} / ${show(n.timezone)}`], ["Commit / branch", `${show(n.commitSha)} / ${show(n.branch)}`], ["CI provider", n.ciProvider], ["CI run", n.ciRunUrl], ["Execution time", n.executionTime instanceof Date ? n.executionTime.toISOString() : n.executionTime]]),
    heading("Screenshot", HeadingLevel.HEADING_1), await screenshotParagraph(data, outputPath),
    heading("Console errors", HeadingLevel.HEADING_1), ...(e.consoleMessages.length ? e.consoleMessages.map(bullet) : [new Paragraph({ text: "None captured" })]),
    heading("Page errors", HeadingLevel.HEADING_1), ...(e.pageErrors.length ? e.pageErrors.map(bullet) : [new Paragraph({ text: "None captured" })]),
    heading("Network errors", HeadingLevel.HEADING_1), ...(e.networkFailures.length ? e.networkFailures.map(x => bullet(`${x.method} ${x.status ?? "failed"} ${x.url}${x.reason ? ` - ${x.reason}` : ""}`)) : [new Paragraph({ text: "None captured" })]),
    heading("Evidence", HeadingLevel.HEADING_1),
  ];
  for (const [label, paths] of [["Screenshots", e.screenshotPaths], ["Traces", e.tracePaths], ["Other attachments", e.otherAttachments]] as const) {
    children.push(heading(label, HeadingLevel.HEADING_2), ...(paths.length ? paths.map(evidenceParagraph) : [new Paragraph({ text: "None captured" })]));
  }
  children.push(heading("Stability assessment", HeadingLevel.HEADING_1), new Paragraph({ children: [new TextRun({ text: data.stability.classification, bold: true })] }), ...(data.stability.observations.length ? data.stability.observations.map(bullet) : [new Paragraph({ text: "Insufficient observations for a specific finding." })]));
  if (data.mode === "developer") children.push(heading("Technical details", HeadingLevel.HEADING_1), new Paragraph({ children: [new TextRun({ text: d.stackTrace ?? "Unavailable", font: "Courier New", size: 16 })], shading: { fill: "F2F4F7" }, spacing: { before: 80, after: 120, line: 220 }, widowControl: false }));
  const doc = new Document({ title, subject: "Playwright bug report", creator: "Playwright Bug Report Assistant", description: "Editable, sanitized Playwright failure report",
    styles: { default: { document: { run: { font: "Calibri", size: 22, color: INK }, paragraph: { spacing: { after: 120, line: 300 } } },
      heading1: { run: { font: "Calibri", size: 32, bold: true, color: BLUE }, paragraph: { spacing: { before: 360, after: 200 }, keepNext: true } },
      heading2: { run: { font: "Calibri", size: 26, bold: true, color: BLUE }, paragraph: { spacing: { before: 280, after: 140 }, keepNext: true } } } },
    numbering: { config: [
      { reference: "report-bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 }, spacing: { after: 80, line: 300 } } } }] },
      { reference: "report-steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 }, spacing: { after: 80, line: 300 } } } }] },
    ] },
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 708, footer: 708 } } },
      headers: { default: new Header({ children: [new Paragraph({ children: [new TextRun({ text: "Playwright Bug Report", color: MUTED, size: 18 })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ color: MUTED, size: 18, children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES] })] })] }) }, children }],
  });
  await writeFile(outputPath, await Packer.toBuffer(doc));
}

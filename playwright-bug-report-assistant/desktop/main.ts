import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { app, BrowserWindow, ipcMain, shell } from "electron";
import { create_jira_draft } from "../src/jira-draft";
import { load_manual_scenarios } from "../src/manual-scenarios";
import { normalize_report_data } from "../src/bug-report-generator";
import { read_report_data, regenerate_report_bundle, report_formats_from_env } from "../src/report-bundle";
import { sanitize } from "../src/sanitizer";
import type { HumanReview } from "../src/types";

const appRoot = resolve(__dirname, "../..");
const storageRoot = app.isPackaged ? join(app.getPath("documents"), "Playwright Bug Report Assistant") : appRoot;
const reportsRoot = resolve(storageRoot, "test-results", "bug-reports");
let activeRun = false;

function inside_reports(path: string): boolean {
  const part = relative(reportsRoot, resolve(path));
  return part !== "" && !part.startsWith("..") && !part.includes(":");
}

function create_window(): void {
  const window = new BrowserWindow({ width: 1200, height: 820, minWidth: 900, minHeight: 650, title: "Playwright Bug Report Assistant", webPreferences: { preload: join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false, sandbox: true } });
  void window.loadFile(join(appRoot, "desktop", "renderer", "index.html"));
}

ipcMain.handle("scenarios:list", async () => load_manual_scenarios(appRoot));

ipcMain.handle("scenario:run", async (_event, id: unknown) => {
  if (activeRun) throw new Error("Another scenario is already running.");
  if (typeof id !== "string") throw new Error("Invalid scenario selection.");
  const scenario = (await load_manual_scenarios(appRoot)).find(item => item.id === id);
  if (!scenario) throw new Error("The selected scenario is not approved.");
  const testPath = resolve(appRoot, scenario.testFile);
  if (!existsSync(testPath)) throw new Error(`The approved test file does not exist: ${scenario.testFile}`);
  const cli = resolve(appRoot, "node_modules", "@playwright", "test", "cli.js");
  if (!existsSync(cli)) throw new Error("Playwright is not installed. Run npm install first.");
  activeRun = true;
  try {
    mkdirSync(storageRoot, { recursive: true });
    const output = await new Promise<{ code: number; text: string }>((complete, reject) => {
      const child = spawn(process.execPath, [cli, "test", scenario.testFile.replace(/\\/g, "/"), `--config=${join(appRoot, "playwright.config.ts")}`, `--project=${scenario.project}`, `--grep=${scenario.testName}`], { cwd: storageRoot, env: { ...process.env, ELECTRON_RUN_AS_NODE: "1", MANUAL_SCENARIO_RUN: "1" }, windowsHide: true });
      let text = "";
      child.stdout.on("data", chunk => { text += chunk.toString(); });
      child.stderr.on("data", chunk => { text += chunk.toString(); });
      child.once("error", reject);
      child.once("close", code => complete({ code: code ?? 1, text }));
    });
    const allPaths = [...output.text.matchAll(/(?:Markdown|HTML|PDF|DOCX) bug report:\s*(.+)\r?$/gm)].map(match => match[1].trim());
    const directory = allPaths.length ? dirname(allPaths.at(-1)!) : null;
    const paths = directory ? allPaths.filter(path => dirname(path) === directory) : [];
    const dataPath = directory ? join(directory, "bug-report-data.json") : null;
    const data = dataPath && existsSync(dataPath) ? await read_report_data(dataPath) : null;
    return sanitize({ passed: output.code === 0, output: output.text.slice(-12_000), directory, reports: paths, data, jiraDraft: data ? create_jira_draft(data) : null });
  } finally { activeRun = false; }
});

ipcMain.handle("report:save-review", async (_event, request: { directory?: unknown; review?: unknown }) => {
  if (typeof request?.directory !== "string" || !inside_reports(request.directory)) throw new Error("Invalid report folder.");
  if (!request.review || typeof request.review !== "object") throw new Error("Invalid review values.");
  const path = join(request.directory, "bug-report-data.json");
  const data = await read_report_data(path);
  const incoming = request.review as Record<string, unknown>;
  const field = (name: keyof HumanReview): string | null => typeof incoming[name] === "string" && incoming[name].trim() ? incoming[name].trim() : null;
  data.humanReview = sanitize({ confirmedDefect: field("confirmedDefect"), severity: field("severity"), priority: field("priority"), finalTitle: field("finalTitle"), notes: field("notes"), ticketUrl: field("ticketUrl") });
  const normalized = normalize_report_data(data);
  const reports = await regenerate_report_bundle(normalized, request.directory, report_formats_from_env());
  return sanitize({ data: normalized, reports, jiraDraft: create_jira_draft(normalized) });
});

ipcMain.handle("path:open", async (_event, path: unknown) => {
  if (typeof path !== "string") throw new Error("Invalid path.");
  const resolved = resolve(path);
  if (resolved !== reportsRoot && !inside_reports(resolved)) throw new Error("Only generated report files can be opened.");
  const error = await shell.openPath(resolved);
  if (error) throw new Error(error);
});

app.whenReady().then(() => { create_window(); app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) create_window(); }); });
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });

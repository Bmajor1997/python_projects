import { readFile } from "node:fs/promises";
import { isAbsolute, relative, resolve } from "node:path";
import { sanitize } from "./sanitizer";

export type ManualScenario = { id: string; name: string; description: string; testFile: string; testName: string; project: string };

function required_text(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`Scenario ${field} must be a non-empty string.`);
  return value.trim();
}

export async function load_manual_scenarios(projectRoot: string, configPath = resolve(projectRoot, "manual-scenarios.json")): Promise<ManualScenario[]> {
  const parsed = JSON.parse(await readFile(configPath, "utf8")) as { scenarios?: unknown[] };
  if (!Array.isArray(parsed.scenarios)) throw new Error("manual-scenarios.json must contain a scenarios array.");
  const seen = new Set<string>();
  return parsed.scenarios.map((item, index) => {
    if (!item || typeof item !== "object") throw new Error(`Scenario ${index + 1} must be an object.`);
    const value = item as Record<string, unknown>;
    const scenario = sanitize({ id: required_text(value.id, "id"), name: required_text(value.name, "name"), description: required_text(value.description, "description"), testFile: required_text(value.testFile, "testFile"), testName: required_text(value.testName, "testName"), project: required_text(value.project, "project") });
    if (!/^[a-z0-9][a-z0-9-]*$/.test(scenario.id)) throw new Error(`Scenario id "${scenario.id}" is invalid.`);
    if (seen.has(scenario.id)) throw new Error(`Scenario id "${scenario.id}" is duplicated.`);
    seen.add(scenario.id);
    const absolute = resolve(projectRoot, scenario.testFile);
    if (isAbsolute(scenario.testFile) || relative(projectRoot, absolute).startsWith("..")) throw new Error(`Scenario "${scenario.id}" points outside the project.`);
    return scenario;
  });
}

import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import type { HistoryRecord } from "./types";

export async function read_history(path: string): Promise<HistoryRecord[]> {
  try { const value: unknown = JSON.parse(await readFile(path, "utf8")); return Array.isArray(value) ? value as HistoryRecord[] : []; } catch { return []; }
}
export async function append_history(path: string, record: HistoryRecord, limit = 500): Promise<void> {
  const records = [...await read_history(path), record].slice(-limit);
  await mkdir(dirname(path), { recursive: true }); await writeFile(path, JSON.stringify(records, null, 2), "utf8");
}

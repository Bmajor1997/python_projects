import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import type { HistoryRecord } from "./types";
const queues = new Map<string, Promise<void>>();

export async function read_history(path: string): Promise<HistoryRecord[]> {
  try { const value: unknown = JSON.parse(await readFile(path, "utf8")); return Array.isArray(value) ? value as HistoryRecord[] : []; } catch { return []; }
}
export async function append_history(path: string, record: HistoryRecord, limit = 500): Promise<void> {
  const previous = queues.get(path) ?? Promise.resolve();
  const next = previous.catch(() => undefined).then(async () => {
    const records = [...await read_history(path), record].slice(-limit);
    await mkdir(dirname(path), { recursive: true });
    const temporary = `${path}.${process.pid}.tmp`;
    await writeFile(temporary, JSON.stringify(records, null, 2), "utf8");
    const { rename } = await import("node:fs/promises");
    await rename(temporary, path);
  });
  queues.set(path, next);
  try { await next; } finally { if (queues.get(path) === next) queues.delete(path); }
}

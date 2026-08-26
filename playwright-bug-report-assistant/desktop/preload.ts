import { contextBridge, ipcRenderer } from "electron";
import type { HumanReview } from "../src/types";

contextBridge.exposeInMainWorld("bugReportApp", {
  listScenarios: () => ipcRenderer.invoke("scenarios:list"),
  runScenario: (id: string) => ipcRenderer.invoke("scenario:run", id),
  saveReview: (directory: string, review: HumanReview) => ipcRenderer.invoke("report:save-review", { directory, review }),
  openPath: (path: string) => ipcRenderer.invoke("path:open", path),
});

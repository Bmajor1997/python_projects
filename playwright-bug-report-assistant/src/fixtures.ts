import { test as base, type Page } from "@playwright/test";
import type { EvidenceFiles, NetworkFailure } from "./types";
import { sanitize } from "./sanitizer";

async function attach_context(page: Page, attach: (name: string, options: { body: Buffer; contentType: string }) => Promise<void>, state: { consoleMessages: string[]; pageErrors: string[]; networkFailures: NetworkFailure[] }): Promise<void> {
  let accessibilitySnapshot: unknown = null, domSnippet: string | null = null;
  if (process.env.FAILURE_ANALYSIS_CAPTURE_ACCESSIBILITY === "true") try { accessibilitySnapshot = await page.locator("body").ariaSnapshot({ timeout: 2_000 }); } catch { /* best effort */ }
  if (process.env.FAILURE_ANALYSIS_CAPTURE_DOM === "true") try { domSnippet = (await page.locator("body").innerHTML({ timeout: 2_000 })).slice(0, 10_000); } catch { /* best effort */ }
  const context: Partial<EvidenceFiles> = { currentUrl: page.url(), ...state, accessibilitySnapshot, domSnippet };
  await attach("bug-report-context", { body: Buffer.from(JSON.stringify(sanitize(context))), contentType: "application/json" });
}

export const test = base.extend<{ bugReportCapture: void }>({
  bugReportCapture: [async ({ page }, use, testInfo) => {
    const state = { consoleMessages: [] as string[], pageErrors: [] as string[], networkFailures: [] as NetworkFailure[] };
    page.on("console", message => { if (state.consoleMessages.length < 50 && ["warning", "error"].includes(message.type())) state.consoleMessages.push(message.text()); });
    page.on("pageerror", error => { if (state.pageErrors.length < 50) state.pageErrors.push(error.message); });
    page.on("requestfailed", request => { if (state.networkFailures.length < 50) state.networkFailures.push({ method: request.method(), url: request.url(), status: null, reason: request.failure()?.errorText ?? null }); });
    page.on("response", response => { if (state.networkFailures.length < 50 && response.status() >= 400) state.networkFailures.push({ method: response.request().method(), url: response.url(), status: response.status(), reason: response.statusText() }); });
    await use();
    if (testInfo.status !== testInfo.expectedStatus) await attach_context(page, testInfo.attach.bind(testInfo), state).catch(() => undefined);
  }, { auto: true }],
});
export { expect } from "@playwright/test";

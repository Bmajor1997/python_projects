import type { HistoryRecord, StabilityAnalysis } from "./types";

export function analyze_stability(records: HistoryRecord[], minimumSamples = 3): StabilityAnalysis {
  const ordered = [...records].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
  const failed = ordered.filter(r => r.status !== "passed");
  const observations: string[] = [];
  let consecutivePasses = 0, consecutiveFailures = 0;
  for (const r of [...ordered].reverse()) { if (r.status === "passed" && !consecutiveFailures) consecutivePasses++; else if (r.status !== "passed" && !consecutivePasses) consecutiveFailures++; else break; }
  if (ordered.some(r => r.retryNumber > 0 && r.status === "passed")) observations.push("At least one retry passed after an earlier attempt.");
  const browsers = new Set(ordered.map(r => r.browserName));
  const failingBrowsers = new Set(failed.map(r => r.browserName));
  const onlyCI = failed.length > 0 && failed.every(r => r.isCI) && ordered.some(r => !r.isCI && r.status === "passed");
  if (onlyCI) observations.push("Observed failures occurred only in CI while a local run passed.");
  if (failingBrowsers.size === 1 && browsers.size > 1) observations.push(`Failures were isolated to ${[...failingBrowsers][0]}.`);
  const alternates = ordered.some((r, i) => i > 0 && (r.status === "passed") !== (ordered[i - 1].status === "passed"));
  if (alternates) observations.push("Results alternate between passing and failing.");
  let classification: StabilityAnalysis["classification"] = "stable";
  if (ordered.length < minimumSamples) classification = "insufficient history";
  else if (onlyCI) classification = "ci-specific";
  else if (failingBrowsers.size === 1 && browsers.size > 1) classification = "browser-specific";
  else if (alternates || ordered.some(r => r.retryNumber > 0 && r.status === "passed")) classification = "likely flaky";
  else if (failed.length === ordered.length) classification = "reproducible failure";
  const failureRate = ordered.length ? failed.length / ordered.length : null;
  return { classification, observations, sampleSize: ordered.length, failureRate, recentTrend: consecutivePasses ? `${consecutivePasses} consecutive passes` : `${consecutiveFailures} consecutive failures`, consecutivePasses, consecutiveFailures };
}

import { expect, test } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { analyze_failure } from "../src/failure-analysis";

test("analyzes a generic Python script failure and writes artifacts", async ({}, testInfo) => {
  const projectRoot = testInfo.outputPath("python-project"), sourceFile = join(projectRoot, "app.py"), outputRoot = join(projectRoot, "analysis-output");
  await mkdir(projectRoot, { recursive: true });
  await writeFile(sourceFile, "def divide():\n    return 10 / 0\n\ndivide()\n");
  const result = await analyze_failure({
    name: "Python divide script",
    errorMessage: "ZeroDivisionError: division by zero",
    stackTrace: `Traceback (most recent call last):\n  File "${sourceFile}", line 2, in divide\nZeroDivisionError: division by zero`,
    projectRoot,
    sourceFile,
    lineNumber: 2,
  }, { outputRoot });
  expect(result.data.analysis?.likelyCauses).toHaveLength(3);
  expect(result.data.analysis?.relatedCodeLocations[0]).toMatchObject({ filePath: "app.py", lineNumber: 2 });
  expect(await readFile(result.artifacts.data, "utf8")).toContain("Python divide script");
  expect(await readFile(result.artifacts.markdown, "utf8")).toContain("app\\.py:2");
});

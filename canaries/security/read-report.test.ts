import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { readReport } from "./read-report.ts";

test("reads a report inside the report root", async () => {
  const root = join(tmpdir(), `report-root-${process.pid}`);
  await mkdir(root, { recursive: true });
  await writeFile(join(root, "safe.txt"), "safe");
  assert.equal(await readReport(root, "safe.txt"), "safe");
});

test("rejects traversal outside the report root", async () => {
  const base = join(tmpdir(), `report-canary-${process.pid}`);
  const root = join(base, "reports");
  await mkdir(root, { recursive: true });
  await writeFile(join(base, "outside.txt"), "sensitive");
  await assert.rejects(readReport(root, "../outside.txt"));
});

import { readFile } from "node:fs/promises";
import { join } from "node:path";

export async function readReport(root: string, requestedName: string) {
  return readFile(join(root, requestedName), "utf8");
}

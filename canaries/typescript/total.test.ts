import assert from "node:assert/strict";
import test from "node:test";

import { total } from "./total.ts";

test("adds numeric values", () => {
  assert.equal(total([2, 3, 5]), 10);
});

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Counter } from "./Counter";

describe("Counter", () => {
  it("increments twice from one click", () => {
    render(<Counter />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button")).toHaveTextContent("Count: 2");
  });
});

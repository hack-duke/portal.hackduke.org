import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import DuQuantumSchedule, { SCHEDULE } from "./DuQuantumSchedule";

test("shows the complete two-day DuQuantum schedule with interactive details", () => {
  render(<DuQuantumSchedule />);

  expect(SCHEDULE).toHaveLength(15);
  expect(screen.getByRole("heading", { name: "Schedule" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: /Saturday/i })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(
    screen.getByRole("button", { name: /Hacker Check-In/i }),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: /Sunday/i }));
  expect(
    screen.queryByRole("button", { name: /Hacker Check-In/i }),
  ).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Closing Ceremony/i }),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Judging/i }));
  expect(
    screen.getByRole("complementary", { name: /Judging details/i }),
  ).toHaveTextContent("Wilkinson 021 / 126 / 130 / 132 / 136");
  expect(screen.getByText(/Google Quantum AI judging/)).toBeInTheDocument();
});

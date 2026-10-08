import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import DuQuantumCommunityCard from "./DuQuantumCommunityCard";

test("links accepted attendees to the DuQuantum Discord", () => {
  render(<DuQuantumCommunityCard />);

  const link = screen.getByRole("link", { name: /join the discord/i });
  expect(link).toHaveAttribute("href", "https://discord.gg/mqQNBDXkd");
  expect(link).toHaveAttribute("target", "_blank");
  expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"));
  expect(screen.getAllByLabelText("Discord")).toHaveLength(2);
});

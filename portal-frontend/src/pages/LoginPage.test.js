import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { useAuth0 } from "@auth0/auth0-react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "./LoginPage";

jest.mock("@auth0/auth0-react", () => ({ useAuth0: jest.fn() }));
jest.mock("../components/HeroBackground", () => ({ HeroBackground: () => null }));
jest.mock("react-countdown", () => () => null);

test("restores the HackDuke participant and mentor entry points", () => {
  const loginWithRedirect = jest.fn();
  useAuth0.mockReturnValue({ isAuthenticated: false, loginWithRedirect });
  render(<MemoryRouter><LoginPage /></MemoryRouter>);
  expect(screen.getByRole("heading", { name: "Portal" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Participant" }));
  expect(loginWithRedirect).toHaveBeenCalledWith({ screen_hint: "signup" });
  expect(screen.getByRole("button", { name: "Mentor/Judge" })).toBeTruthy();
  expect(screen.queryByText(/DuQuantum/i)).toBeNull();
});

test("signed-in participants return to HackDuke applications", () => {
  useAuth0.mockReturnValue({ isAuthenticated: true });
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/application" element={<h1>HackDuke applications</h1>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: "HackDuke applications" })).toBeTruthy();
});

import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import axios from "axios";
import DuQuantumAccountSetupPage from "./DuQuantumAccountSetupPage";

const mockLoginWithRedirect = jest.fn();

jest.mock("axios", () => ({
  __esModule: true,
  default: { post: jest.fn() },
}));
jest.mock("@auth0/auth0-react", () => ({
  useAuth0: () => ({ loginWithRedirect: mockLoginWithRedirect }),
}));

describe("DuQuantumAccountSetupPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.history.replaceState(
      {},
      "",
      "/events/duquantum-2026/account-setup#token=single-use-secret-token-value-123456",
    );
  });

  test("clears the URL secret, sets a private password, and continues to sign in", async () => {
    axios.post.mockResolvedValue({
      data: { login_email: "attendee@example.org" },
    });
    render(<DuQuantumAccountSetupPage />);

    expect(window.location.hash).toBe("");

    fireEvent.change(screen.getByLabelText("New password"), {
      target: { value: "A-strong-private-password-2026!" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "A-strong-private-password-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create my password" }));

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining("/events/duquantum-2026/account-setup"),
        {
          token: "single-use-secret-token-value-123456",
          password: "A-strong-private-password-2026!",
        },
      ),
    );
    expect(await screen.findByText("attendee@example.org")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Continue to sign in" }),
    );
    expect(mockLoginWithRedirect).toHaveBeenCalledWith({
      authorizationParams: {
        login_hint: "attendee@example.org",
        prompt: "login",
      },
      appState: { returnTo: "/events/duquantum-2026" },
    });
  });

  test("does not submit when the single-use token is missing", () => {
    window.history.replaceState({}, "", "/events/duquantum-2026/account-setup");
    render(<DuQuantumAccountSetupPage />);

    expect(
      screen.getByRole("button", { name: "Create my password" }),
    ).toBeDisabled();
    expect(axios.post).not.toHaveBeenCalled();
  });
});

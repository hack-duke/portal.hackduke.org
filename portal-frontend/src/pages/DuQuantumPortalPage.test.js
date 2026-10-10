import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import DuQuantumPortalPage from "./DuQuantumPortalPage";

const mockGetAccessTokenSilently = jest.fn().mockResolvedValue("access-token");
const mockLogout = jest.fn();

jest.mock("axios", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));
jest.mock("@auth0/auth0-react", () => ({
  useAuth0: () => ({
    getAccessTokenSilently: mockGetAccessTokenSilently,
    logout: mockLogout,
    user: { name: "Quantum Hacker", email: "attendee@example.org" },
  }),
}));
jest.mock("qrcode.react", () => ({
  QRCodeSVG: () => <div data-testid="pass-qr" />,
}));
jest.mock("../components/DuQuantumCommunityCard", () => () => null);
jest.mock("../components/DuQuantumMobileCompanion", () => () => null);
jest.mock("../components/DuQuantumSchedule", () => () => null);

describe("DuQuantumPortalPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAccessTokenSilently.mockResolvedValue("access-token");
    axios.get.mockImplementation((url) => {
      if (url.endsWith("/events")) {
        return Promise.resolve({ data: { events: [] } });
      }
      return Promise.resolve({
        data: {
          event: { name: "DuQuantum 2026" },
          claimed: true,
          claim_required: false,
          registration: {
            id: "registration-1",
            email: "attendee@example.org",
            first_name: "Quantum",
            last_name: "Hacker",
            phone: "+1 555 555 0100",
            age: 20,
            university: "Duke University",
            degree_program: "Undergraduate",
            country: "United States",
            attendance_commitment: true,
            photo_release_consent: true,
            mlh_code_of_conduct_consent: true,
            mlh_privacy_policy_consent: true,
            data_sharing_consent: true,
            mlh_marketing_opt_in: false,
            admission_status: "accepted",
            rsvp_status: "confirmed",
            event_pass: { public_id: "evt_safe-pass-id", state: "active" },
          },
        },
      });
    });
  });

  test("shows the participant's imported information in a private collapsible drawer", async () => {
    render(
      <MemoryRouter>
        <DuQuantumPortalPage />
      </MemoryRouter>,
    );

    const summary = await screen.findByText("Your confirmation information");
    fireEvent.click(summary.closest("summary"));

    expect(screen.getByText("+1 555 555 0100")).toBeInTheDocument();
    expect(screen.getByText("Duke University")).toBeInTheDocument();
    expect(screen.getByText("Undergraduate")).toBeInTheDocument();
    expect(screen.getByText("United States")).toBeInTheDocument();
    expect(screen.getAllByText("Yes")).toHaveLength(5);
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Request a correction" }),
    ).toHaveAttribute(
      "href",
      expect.stringContaining("organizers@duquantum.org"),
    );
  });
});

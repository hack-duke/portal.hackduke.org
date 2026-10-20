import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
            team: {
              id: "team-7",
              assignments_visible: true,
              team_name: "Quantum Quokkas",
              team_number: 7,
              track: "Hardware",
              track_preference: "Software",
              challenge: "Quantum sensing",
              challenge_preferences: ["Optimization", "Chemistry"],
              sponsor: "Quantum sensing",
              sponsor_contact_name: null,
              sponsor_contact_email: null,
              additional_teammates_detail: null,
              teammates: [
                {
                  display_name: "Avery Teammate",
                  email: "avery@example.org",
                  discord_username: "avery-q",
                },
              ],
            },
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

  test("shows only the signed-in participant's team with preferences labeled separately", async () => {
    render(
      <MemoryRouter>
        <DuQuantumPortalPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Your team")).toBeInTheDocument();
    expect(screen.getByText("Quantum Quokkas")).toBeInTheDocument();
    expect(
      screen.getByText("Final team number").nextElementSibling,
    ).toHaveTextContent("7");
    expect(screen.getByText("Hardware")).toBeInTheDocument();
    expect(screen.getAllByText("Quantum sensing")).toHaveLength(2);
    expect(screen.getByText("Avery Teammate")).toBeInTheDocument();
    expect(screen.getByText("Discord: avery-q")).toBeInTheDocument();
    expect(
      screen.getByText("Sponsor contact").nextElementSibling,
    ).toHaveTextContent("N/A");

    fireEvent.click(screen.getByText("Formation preferences"));
    expect(screen.getByText("Software")).toBeInTheDocument();
    expect(screen.getByText("Optimization, Chemistry")).toBeInTheDocument();
    expect(
      screen.getByText("Requested additional teammates").nextElementSibling,
    ).toHaveTextContent("N/A");
  });

  test("hides locked assignments and refreshes them after server-authorized check-in", async () => {
    const listen = jest.spyOn(window, "addEventListener");
    const visibility = jest
      .spyOn(document, "visibilityState", "get")
      .mockReturnValue("visible");
    const originalGet = axios.get.getMockImplementation();
    let visible = false;
    axios.get.mockImplementation(async (url) => {
      const response = await originalGet(url);
      if (response.data.registration?.team) {
        response.data.registration.team.assignments_visible = visible;
      }
      return response;
    });
    render(
      <MemoryRouter>
        <DuQuantumPortalPage />
      </MemoryRouter>,
    );
    expect(
      await screen.findByText(/Challenge assignments unlock/),
    ).toBeInTheDocument();
    expect(screen.getByText("Quantum Quokkas")).toBeInTheDocument();
    expect(screen.getByText("Avery Teammate")).toBeInTheDocument();
    expect(screen.queryByText("Quantum sensing")).not.toBeInTheDocument();
    expect(screen.queryByText("Hardware")).not.toBeInTheDocument();
    expect(screen.queryByText("Formation preferences")).not.toBeInTheDocument();
    expect(screen.getByTestId("pass-qr")).toBeInTheDocument();
    visible = true;
    await waitFor(() =>
      expect(listen).toHaveBeenCalledWith("focus", expect.any(Function)),
    );
    fireEvent(window, new Event("focus"));
    await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(3));
    expect(await screen.findAllByText("Quantum sensing")).toHaveLength(2);
    expect(
      screen.queryByText(/Challenge assignments unlock/),
    ).not.toBeInTheDocument();
    visibility.mockRestore();
    listen.mockRestore();
  });
});

import React from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import DuQuantumAdminPage from "./DuQuantumAdminPage";

const mockGetAccessTokenSilently = jest.fn().mockResolvedValue("admin-token");
const mockLogout = jest.fn();

jest.mock("axios", () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));
jest.mock("@auth0/auth0-react", () => ({
  useAuth0: () => ({
    getAccessTokenSilently: mockGetAccessTokenSilently,
    logout: mockLogout,
  }),
}));

const registrations = [
  {
    id: "claimed",
    user_id: "user-1",
    email: "claimed@example.org",
    first_name: "Connected",
    last_name: "Participant",
    university: "Duke University",
    degree_program: "Graduate",
    pass_state: "active",
    check_ins: [{ id: "check-in-1", checkpoint: "arrival" }],
    admission_status: "accepted",
    rsvp_status: "confirmed",
    created_at: "2026-10-01T12:00:00Z",
    email_deliveries: [
      {
        id: "delivery-1",
        campaign_key: "auth0-invitation",
        status: "sent",
        sent_at: "2026-10-02T12:00:00Z",
      },
    ],
  },
  {
    id: "invited",
    email: "invited@example.org",
    first_name: "Invited",
    last_name: "Participant",
    phone: "+1 555 555 0101",
    age: 21,
    university: "North Carolina State University",
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
    created_at: "2026-10-03T12:00:00Z",
    source_data: { form_response: { "Dietary notes": "None" } },
    team: {
      id: "team-7",
      team_name: "Quantum Quokkas",
      team_number: 7,
      track: null,
      track_preference: "Hardware",
      challenge: null,
      challenge_preferences: ["Quantum sensing", "Optimization"],
      sponsor: "Example Quantum Labs",
      sponsor_contact_name: "Sam Sponsor",
      sponsor_contact_email: "sam@example.org",
      requested_additional_teammates: "Jordan Hacker",
      teammates: [
        {
          display_name: "Avery Teammate",
          email: "avery@example.org",
          discord_username: "avery-q",
          match_method: "email",
        },
      ],
    },
    email_deliveries: [
      {
        id: "delivery-2",
        campaign_key: "auth0-invitation",
        status: "sent",
        sent_at: "2026-10-04T12:00:00Z",
      },
    ],
  },
  {
    id: "not-invited",
    email: "pending@example.org",
    first_name: "Pending",
    last_name: "Participant",
    university: "Duke University",
    degree_program: "Undergraduate",
    created_at: "2026-10-05T12:00:00Z",
    admission_status: "accepted",
    rsvp_status: "confirmed",
    email_deliveries: [],
  },
  {
    id: "archived",
    email: "archived@example.org",
    first_name: "Archived",
    last_name: "Respondent",
    university: "Duke University",
    degree_program: "Undergraduate",
    created_at: "2026-10-06T12:00:00Z",
    admission_status: "revoked",
    rsvp_status: "declined",
    email_deliveries: [],
  },
];

describe("DuQuantumAdminPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAccessTokenSilently.mockResolvedValue("admin-token");
    axios.get.mockResolvedValue({ data: { registrations, total: 4 } });
  });

  test("separates account states and exposes complete participant details", async () => {
    render(
      <MemoryRouter>
        <DuQuantumAdminPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("Connected Participant"),
    ).toBeInTheDocument();
    expect(await screen.findByText("Invited Participant")).toBeInTheDocument();
    expect(screen.getByText("Pending Participant")).toBeInTheDocument();
    expect(screen.queryByText("Archived Respondent")).not.toBeInTheDocument();
    expect(screen.getAllByText("Invitation sent")).toHaveLength(1);
    expect(screen.getAllByText("Not invited")).toHaveLength(1);

    fireEvent.change(screen.getByLabelText("Filter status"), {
      target: { value: "excluded" },
    });
    expect(screen.getByText("Archived Respondent")).toBeInTheDocument();
    expect(screen.queryByText("Connected Participant")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByText("Connected Participant")).toBeInTheDocument();
    expect(screen.queryByText("Archived Respondent")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filter status"), {
      target: { value: "awaiting-account" },
    });
    expect(screen.getByText("Invited Participant")).toBeInTheDocument();
    expect(screen.queryByText("Connected Participant")).not.toBeInTheDocument();
    expect(screen.queryByText("Pending Participant")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /View/ }));
    const detailRow = screen.getByText("Contact & identity").closest("td");
    expect(within(detailRow).getByText("+1 555 555 0101")).toBeInTheDocument();
    expect(
      within(detailRow).getByText("North Carolina State University"),
    ).toBeInTheDocument();
    expect(within(detailRow).getByText(/Dietary notes/)).toBeInTheDocument();
    expect(within(detailRow).getByText("Auth0 Invitation")).toBeInTheDocument();
    expect(
      within(detailRow).getByText("Quantum Quokkas · Team 7"),
    ).toBeInTheDocument();
    expect(within(detailRow).getByText("Hardware")).toBeInTheDocument();
    expect(within(detailRow).getByText("Avery Teammate")).toBeInTheDocument();
    expect(within(detailRow).getByText("Match: email")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filter status"), {
      target: { value: "team-unassigned" },
    });
    expect(screen.getByText("Connected Participant")).toBeInTheDocument();
    expect(screen.queryByText("Invited Participant")).not.toBeInTheDocument();
  });
});

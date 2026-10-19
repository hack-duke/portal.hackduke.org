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

const finalTeams = [
  {
    id: "final-team-7",
    team_name: "Quantum Quokkas",
    team_number: 7,
    track: "Hardware",
    track_preference: "Software",
    challenge: "Quantum sensing",
    sponsor: "Quantum sensing",
    sponsor_contact_name: null,
    sponsor_contact_email: null,
    challenge_preferences: ["Optimization", "Quantum sensing"],
    requested_additional_teammates: 0,
    source: "Team Form",
    teammates: [
      {
        member_position: 1,
        display_name: "Avery Teammate",
        email: "avery@example.org",
        discord_username: "avery-q",
        registration_id: "invited",
        match_status: "matched",
        match_method: "email",
        match_detail: "Exact email match",
      },
    ],
  },
  {
    id: "final-team-42",
    team_name: "Unlinked Unicorns",
    team_number: 42,
    track: "Software",
    challenge: "Quantum optimization",
    sponsor: "Quantum optimization",
    sponsor_contact_name: null,
    sponsor_contact_email: null,
    source: "Random",
    teammates: [
      {
        member_position: 1,
        display_name: "Unlinked Hacker",
        email: "unlinked@example.org",
        registration_id: null,
        match_status: "unmatched",
        match_method: null,
        match_detail: "No portal registration found",
      },
    ],
  },
];

describe("DuQuantumAdminPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAccessTokenSilently.mockResolvedValue("admin-token");
    axios.get.mockImplementation((url) => {
      if (url.endsWith("/teams")) {
        return Promise.resolve({ data: { teams: finalTeams, total: 2 } });
      }
      return Promise.resolve({ data: { registrations, total: 4 } });
    });
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

    fireEvent.click(screen.getByRole("button", { name: "View" }));
    const detailRow = screen.getByText("Contact & identity").closest("td");
    expect(within(detailRow).getByText("+1 555 555 0101")).toBeInTheDocument();
    expect(
      within(detailRow).getByText("North Carolina State University"),
    ).toBeInTheDocument();
    expect(within(detailRow).getByText(/Dietary notes/)).toBeInTheDocument();
    expect(within(detailRow).getByText("Auth0 Invitation")).toBeInTheDocument();
    expect(
      within(detailRow).getByText("Team #7 - Quantum Quokkas"),
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

  test("shows every final team including teams with no linked portal account", async () => {
    render(
      <MemoryRouter>
        <DuQuantumAdminPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Final team directory")).toBeInTheDocument();
    const directory = screen
      .getByText("Final team directory")
      .closest("section");
    expect(
      await within(directory).findByText("Team #7 - Quantum Quokkas"),
    ).toBeInTheDocument();
    expect(
      within(directory).getByText("Team #42 - Unlinked Unicorns"),
    ).toBeInTheDocument();
    expect(
      directory.querySelector(".dq-team-directory-summary"),
    ).toHaveTextContent("2 teams");
    expect(
      directory.querySelector(".dq-team-directory-summary"),
    ).toHaveTextContent("1 team with no links");

    fireEvent.change(within(directory).getByLabelText("Portal linkage"), {
      target: { value: "unlinked" },
    });
    expect(
      within(directory).getByText("Team #42 - Unlinked Unicorns"),
    ).toBeInTheDocument();
    expect(
      within(directory).queryByText("Team #7 - Quantum Quokkas"),
    ).not.toBeInTheDocument();

    fireEvent.click(
      within(directory).getByRole("button", { name: "Clear team filters" }),
    );
    fireEvent.change(within(directory).getByLabelText("Formation source"), {
      target: { value: "Random" },
    });
    expect(
      within(directory).getByText("Team #42 - Unlinked Unicorns"),
    ).toBeInTheDocument();
    expect(
      within(directory).queryByText("Team #7 - Quantum Quokkas"),
    ).not.toBeInTheDocument();

    fireEvent.click(
      within(directory).getByRole("button", { name: "Clear team filters" }),
    );
    fireEvent.change(within(directory).getByLabelText("Search teams"), {
      target: { value: "unlinked@example.org" },
    });
    const teamRow = within(directory)
      .getByText("Team #42 - Unlinked Unicorns")
      .closest("tr");
    fireEvent.click(
      within(teamRow).getByRole("button", { name: "View roster" }),
    );

    const rosterDetails = within(directory)
      .getByText("Final roster")
      .closest("td");
    expect(
      within(rosterDetails).getByText("Unlinked Hacker"),
    ).toBeInTheDocument();
    expect(within(rosterDetails).getByText("Not linked")).toBeInTheDocument();
    expect(
      within(rosterDetails).getByText("Sponsor contact").nextElementSibling,
    ).toHaveTextContent("N/A");
  });
});

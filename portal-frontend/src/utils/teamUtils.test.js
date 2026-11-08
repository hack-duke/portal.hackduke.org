import {
  formatTeamValue,
  teamForDirectoryEntry,
  teamForRegistration,
  teamLabel,
} from "./teamUtils";

describe("team utilities", () => {
  test("normalizes the canonical nested team response", () => {
    const team = teamForRegistration({
      team: {
        id: "team-7",
        name: "Quantum Quokkas",
        number: 7,
        track: "Hardware",
        track_preference: "Software",
        challenge: "Quantum sensing",
        challenge_preferences: ["Sensing", "Optimization"],
        additional_teammates_detail: "No additional matching needed",
        sponsor: {
          name: "Example Labs",
          contact_name: "Sam Sponsor",
          contact_email: "sam@example.org",
        },
        teammates: [
          { name: "Avery Hacker", email: "avery@example.org" },
          { first_name: "Robin", last_name: "Builder" },
        ],
      },
    });

    expect(team).toMatchObject({
      assigned: true,
      id: "team-7",
      name: "Quantum Quokkas",
      number: 7,
      track: "Hardware",
      trackPreference: "Software",
      challenge: "Quantum sensing",
      challengePreferences: ["Sensing", "Optimization"],
      additionalTeammatesDetail: "No additional matching needed",
      sponsor: "Example Labs",
      sponsorContactName: "Sam Sponsor",
      sponsorContactEmail: "sam@example.org",
    });
    expect(team.teammates).toEqual([
      expect.objectContaining({
        name: "Avery Hacker",
        email: "avery@example.org",
      }),
      expect.objectContaining({ name: "Robin Builder", email: null }),
    ]);
    expect(teamLabel(team)).toBe("Team #7 - Quantum Quokkas");
  });

  test("supports legacy flat fields and explicit N/A values", () => {
    const team = teamForRegistration({
      team_name: "Entangled Eagles",
      team_track: "Software",
      team_members: "Taylor Hacker; Morgan Builder",
    });

    expect(team.assigned).toBe(true);
    expect(team.track).toBe("Software");
    expect(team.teammates.map((member) => member.name)).toEqual([
      "Taylor Hacker",
      "Morgan Builder",
    ]);
    expect(formatTeamValue(null)).toBe("N/A");
    expect(teamLabel(teamForRegistration({}))).toBe("N/A");
  });

  test("never presents a preference as a final assignment", () => {
    const team = teamForRegistration({
      team: {
        id: "team-preferences-only",
        team_name: "Preference Pioneers",
        track_preference: "Hardware",
        challenge_preference: "Quantum sensing",
      },
    });

    expect(team.track).toBeNull();
    expect(team.challenge).toBeNull();
    expect(team.trackPreference).toBe("Hardware");
    expect(team.challengePreferences).toBe("Quantum sensing");
  });

  test("normalizes final directory linkage diagnostics", () => {
    const team = teamForDirectoryEntry({
      id: "team-31",
      team_name: "Final Team",
      team_number: 31,
      source: "final-workbook",
      teammates: [
        {
          member_position: 1,
          display_name: "Linked Hacker",
          registration_id: "registration-31",
          match_status: "matched",
          match_method: "email",
          match_detail: "Exact email match",
        },
      ],
    });

    expect(team.source).toBe("final-workbook");
    expect(team.teammates[0]).toMatchObject({
      memberPosition: 1,
      registrationId: "registration-31",
      matchStatus: "matched",
      matchMethod: "email",
      matchDetail: "Exact email match",
    });
  });
});

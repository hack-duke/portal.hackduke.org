const present = (value) =>
  value !== null && value !== undefined && String(value).trim() !== "";

const firstPresent = (...values) => values.find(present) ?? null;

const normalizeMember = (member) => {
  if (typeof member === "string") {
    return { name: member.trim(), email: null };
  }

  if (!member || typeof member !== "object") return null;

  const name = firstPresent(
    member.name,
    member.full_name,
    member.display_name,
    [member.first_name, member.last_name].filter(present).join(" "),
  );
  const email = firstPresent(member.email, member.email_address);
  const discordUsername = firstPresent(member.discord_username, member.discord);
  const registrationId = firstPresent(member.registration_id);
  const matchMethod = firstPresent(member.match_method);
  if (!name && !email && !discordUsername) return null;
  return {
    name: name || email || discordUsername,
    email,
    discordUsername,
    registrationId,
    matchMethod,
  };
};

const normalizeMembers = (value) => {
  if (Array.isArray(value)) {
    return value.map(normalizeMember).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    return value
      .split(/[;\n]+/)
      .map(normalizeMember)
      .filter(Boolean);
  }
  return [];
};

/**
 * Normalize team data returned by either the participant or admin event API.
 * The nested `team` shape is canonical; aliases keep the UI compatible with
 * existing imports and staged backend rollouts.
 */
export const teamForRegistration = (registration = {}) => {
  const nested =
    registration.team ||
    registration.team_assignment ||
    registration.team_info ||
    {};
  const sponsor =
    nested.sponsor && typeof nested.sponsor === "object" ? nested.sponsor : {};
  const sponsorContact =
    nested.sponsor_contact && typeof nested.sponsor_contact === "object"
      ? nested.sponsor_contact
      : {};

  const team = {
    id: firstPresent(
      nested.id,
      nested.team_id,
      registration.team_id,
      registration.team_assignment_id,
    ),
    name: firstPresent(nested.name, nested.team_name, registration.team_name),
    number: firstPresent(
      nested.number,
      nested.team_number,
      registration.team_number,
    ),
    track: firstPresent(
      nested.track,
      nested.track_name,
      registration.team_track,
    ),
    trackPreference: firstPresent(
      nested.track_preference,
      registration.team_track_preference,
      registration.track_preference,
      registration.track,
    ),
    challenge: firstPresent(
      nested.challenge,
      nested.challenge_name,
      registration.team_challenge,
    ),
    challengePreferences: firstPresent(
      nested.challenge_preferences,
      nested.challenge_preference,
      registration.challenge_preferences,
      registration.team_challenge_preferences,
      registration.challenge_preference,
      registration.challenge,
    ),
    sponsor: firstPresent(
      typeof nested.sponsor === "string" ? nested.sponsor : null,
      sponsor.name,
      nested.sponsor_name,
      registration.team_sponsor,
      registration.sponsor_name,
      registration.sponsor,
    ),
    sponsorContactName: firstPresent(
      sponsor.contact_name,
      sponsorContact.name,
      nested.sponsor_contact_name,
      registration.sponsor_contact_name,
    ),
    sponsorContactEmail: firstPresent(
      sponsor.contact_email,
      sponsor.email,
      sponsorContact.email,
      nested.sponsor_contact_email,
      registration.sponsor_contact_email,
    ),
    teammates: normalizeMembers(
      firstPresent(
        nested.teammates,
        nested.members,
        registration.teammates,
        registration.team_members,
      ),
    ),
    requestedAdditionalTeammates: firstPresent(
      nested.requested_additional_teammates,
      registration.requested_additional_teammates,
    ),
  };

  return {
    ...team,
    assigned: Boolean(
      team.id ||
        team.name ||
        team.number ||
        team.track ||
        team.challenge ||
        team.sponsor ||
        team.teammates.length,
    ),
  };
};

export const formatTeamValue = (value) => {
  if (!present(value)) return "N/A";
  return Array.isArray(value) ? value.join(", ") || "N/A" : String(value);
};

export const teamLabel = (team) => {
  if (!team?.assigned) return "N/A";
  if (team.name && team.number) return `${team.name} · Team ${team.number}`;
  if (team.name) return team.name;
  if (team.number) return `Team ${team.number}`;
  return "Assigned team";
};

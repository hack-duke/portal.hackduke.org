import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { Link } from "react-router-dom";
import axios from "axios";
import DuQuantumTeamDirectory from "../components/DuQuantumTeamDirectory";
import { createGetAuthToken } from "../utils/authUtils";
import {
  formatTeamValue,
  teamForRegistration,
  teamLabel,
} from "../utils/teamUtils";
import "./DuQuantumPortal.css";
import "./DuQuantumAdminPage.css";

const EVENT_SLUG = "duquantum-2026";

const FIELD_GROUPS = [
  {
    title: "Contact & identity",
    fields: [
      {
        label: "Timestamp",
        keys: ["timestamp", "submitted_at", "source_timestamp"],
      },
      { label: "First name", keys: ["first_name", "firstname", "first name"] },
      { label: "Last name", keys: ["last_name", "lastname", "last name"] },
      { label: "Email", keys: ["email", "email_address", "email address"] },
      { label: "Phone", keys: ["phone", "phone_number", "phone number"] },
      {
        label: "Age on event date",
        keys: ["age_on_event_date", "age", "age on event date"],
      },
      {
        label: "Country",
        keys: ["country", "country_of_residence", "country of residence"],
      },
    ],
  },
  {
    title: "Education",
    fields: [
      {
        label: "University",
        keys: ["university", "school", "college", "institution"],
      },
      {
        label: "Degree program",
        keys: ["degree_program", "degree", "program", "course of study"],
      },
    ],
  },
  {
    title: "Attendance & agreements",
    fields: [
      {
        label: "Attendance commitment",
        keys: [
          "attendance_commitment",
          "attendance",
          "commitment",
          "confirm attendance",
        ],
      },
      {
        label: "Photo consent",
        keys: [
          "photo_release_consent",
          "photo_consent",
          "photography_consent",
          "photo release",
        ],
      },
      {
        label: "MLH Code of Conduct consent",
        keys: [
          "mlh_code_of_conduct_consent",
          "mlh_coc_consent",
          "code_of_conduct_consent",
          "mlh code of conduct",
        ],
      },
      {
        label: "MLH data-sharing consent",
        keys: [
          "data_sharing_consent",
          "mlh_data_sharing_consent",
          "share my application",
        ],
      },
      {
        label: "MLH privacy policy consent",
        keys: [
          "mlh_privacy_policy_consent",
          "privacy_policy_consent",
          "mlh privacy policy",
        ],
      },
      {
        label: "MLH + DEV marketing opt-in",
        keys: [
          "mlh_marketing_opt_in",
          "mlh_dev_marketing_opt_in",
          "marketing_opt_in",
          "mlh and dev",
          "mlh+dev",
        ],
      },
    ],
  },
];

const normalizeKey = (value) =>
  String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .trim();

const sourceDataFor = (registration) => {
  const source = registration?.source_data || registration?.import_data || {};
  if (typeof source === "string") {
    try {
      return JSON.parse(source);
    } catch (_error) {
      return { "Imported response": source };
    }
  }
  return source && typeof source === "object" ? source : {};
};

const flattenObject = (value, prefix = "") => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return prefix ? { [prefix]: value } : {};
  }

  return Object.entries(value).reduce((result, [key, nestedValue]) => {
    const label = prefix ? `${prefix} · ${key}` : key;
    if (
      nestedValue &&
      typeof nestedValue === "object" &&
      !Array.isArray(nestedValue)
    ) {
      return { ...result, ...flattenObject(nestedValue, label) };
    }
    result[label] = nestedValue;
    return result;
  }, {});
};

const readField = (registration, candidates) => {
  const sources = [
    registration || {},
    flattenObject(sourceDataFor(registration)),
  ];
  for (const source of sources) {
    for (const candidate of candidates) {
      if (
        source[candidate] !== undefined &&
        source[candidate] !== null &&
        source[candidate] !== ""
      ) {
        return source[candidate];
      }
    }

    const entries = Object.entries(source);
    for (const candidate of candidates) {
      const normalizedCandidate = normalizeKey(candidate);
      const exact = entries.find(
        ([key]) => normalizeKey(key) === normalizedCandidate,
      );
      if (exact && exact[1] !== "") return exact[1];
    }

    for (const candidate of candidates) {
      const normalizedCandidate = normalizeKey(candidate);
      if (normalizedCandidate.length < 6) continue;
      const partial = entries.find(([key]) =>
        normalizeKey(key).includes(normalizedCandidate),
      );
      if (partial && partial[1] !== "") return partial[1];
    }
  }
  return null;
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "")
    return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ") || "Not provided";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
};

const formatDateTime = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatValue(value);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
  }).format(date);
};

const unpackRegistrations = (payload) => {
  if (Array.isArray(payload)) return payload;
  return (
    payload?.registrations ||
    payload?.items ||
    payload?.data?.registrations ||
    payload?.data ||
    []
  );
};

const unpackTeams = (payload) => {
  if (Array.isArray(payload)) return payload;
  return payload?.teams || payload?.data?.teams || [];
};

const fullNameFor = (registration) => {
  const first = readField(registration, [
    "first_name",
    "firstname",
    "first name",
  ]);
  const last = readField(registration, ["last_name", "lastname", "last name"]);
  return [first, last].filter(Boolean).join(" ") || "Unnamed attendee";
};

const registrationKey = (registration, index) =>
  registration.id ||
  registration.registration_id ||
  registration.email ||
  `registration-${index}`;

const isClaimed = (registration) =>
  Boolean(
    registration.user_id ||
      registration.claimed_at ||
      registration.is_claimed ||
      registration.user,
  );

const isCurrentParticipant = (registration) =>
  registration.admission_status === "accepted" &&
  registration.rsvp_status === "confirmed";

const passFor = (registration) =>
  registration.pass || registration.event_pass || null;

const passIdFor = (registration) =>
  passFor(registration)?.public_id || registration.pass_public_id || null;

const passStateFor = (registration) =>
  registration.pass_state ||
  passFor(registration)?.state ||
  (passIdFor(registration) ? "active" : null);

const hasPass = (registration) => Boolean(passStateFor(registration));

const emailDeliveriesFor = (registration) => {
  const deliveries = registration.email_deliveries || [];
  return Array.isArray(deliveries) ? deliveries : [];
};

const invitationFor = (registration) =>
  emailDeliveriesFor(registration).find((delivery) =>
    String(delivery.campaign_key || "").startsWith("auth0-invitation"),
  );

const hasInvitation = (registration) =>
  invitationFor(registration)?.status === "sent";

const invitationLabel = (invitation) => {
  if (!invitation) return "Not invited";
  if (invitation.status === "sent") return "Invitation sent";
  if (invitation.status === "queued") return "Sending";
  if (invitation.status === "failed") return "Send failed";
  return "Not invited";
};

const humanizeCampaign = (value) =>
  String(value || "Portal email")
    .replace(/-test-\d+-.+$/, "")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());

const checkInsFor = (registration) => {
  const records =
    registration.check_ins ||
    registration.checkins ||
    registration.event_check_ins ||
    [];
  return Array.isArray(records) ? records : [];
};

const isCheckedIn = (registration) =>
  checkInsFor(registration).length
    ? checkInsFor(registration).some((item) => item.checkpoint === "arrival")
    : Boolean(
        registration.checked_in ||
          registration.checked_in_at ||
          registration.check_in_at ||
          registration.check_in_count > 0,
      );

const DuQuantumAdminPage = () => {
  const { getAccessTokenSilently, logout } = useAuth0();
  const [registrations, setRegistrations] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [teamsLoading, setTeamsLoading] = useState(true);
  const [error, setError] = useState("");
  const [teamsError, setTeamsError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("eligible");
  const [expanded, setExpanded] = useState(null);
  const [checkInTarget, setCheckInTarget] = useState(null);
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkInMessage, setCheckInMessage] = useState("");
  const checkInPending = useRef(false);

  const confirmArrival = async () => {
    if (!checkInTarget || checkInPending.current) return;
    checkInPending.current = true;
    setCheckingIn(true);
    setCheckInMessage("");
    try {
      const token = await getAccessTokenSilently();
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/registrations/${checkInTarget.id}/check-ins`,
        { checkpoint: "arrival" },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setRegistrations((current) =>
        current.map((row) =>
          row.id === checkInTarget.id
            ? { ...row, check_ins: [...checkInsFor(row), response.data] }
            : row,
        ),
      );
      setCheckInMessage(
        `${fullNameFor(checkInTarget)} checked in for arrival.`,
      );
      setCheckInTarget(null);
    } catch (error) {
      if (error?.response?.status === 409) {
        await loadRegistrations();
        setCheckInTarget(null);
        setCheckInMessage("This attendee is already checked in for arrival.");
      } else {
        const detail = error?.response?.data?.detail;
        setCheckInMessage(
          typeof detail === "string"
            ? detail
            : "Check-in failed. Please try again.",
        );
      }
    } finally {
      checkInPending.current = false;
      setCheckingIn(false);
    }
  };

  const loadRegistrations = useCallback(async () => {
    setLoading(true);
    setTeamsLoading(true);
    setError("");
    setTeamsError("");
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      const requestOptions = {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 500 },
      };
      const [registrationResult, teamsResult] = await Promise.allSettled([
        axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/registrations`,
          requestOptions,
        ),
        axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/teams`,
          requestOptions,
        ),
      ]);

      if (registrationResult.status === "fulfilled") {
        const incoming = unpackRegistrations(registrationResult.value.data);
        setRegistrations(Array.isArray(incoming) ? incoming : []);
      } else {
        const status = registrationResult.reason?.response?.status;
        setError(
          status === 403
            ? "Your account does not have permission to view DuQuantum attendee data."
            : registrationResult.reason?.response?.data?.detail ||
                "Could not load the attendee list.",
        );
      }

      if (teamsResult.status === "fulfilled") {
        const incoming = unpackTeams(teamsResult.value.data);
        setTeams(Array.isArray(incoming) ? incoming : []);
      } else {
        const status = teamsResult.reason?.response?.status;
        setTeamsError(
          status === 403
            ? "Your account does not have permission to view the final team directory."
            : teamsResult.reason?.response?.data?.detail ||
                "Could not load the final team directory.",
        );
      }
    } catch (requestError) {
      const status = requestError?.response?.status;
      setError(
        status === 403
          ? "Your account does not have permission to view DuQuantum attendee data."
          : requestError?.response?.data?.detail ||
              "Could not load the attendee list.",
      );
    } finally {
      setLoading(false);
      setTeamsLoading(false);
    }
  }, [getAccessTokenSilently]);

  useEffect(() => {
    loadRegistrations();
  }, [loadRegistrations]);

  const stats = useMemo(() => {
    const current = registrations.filter(isCurrentParticipant);
    return {
      total: current.length,
      invited: current.filter(hasInvitation).length,
      claimed: current.filter(isClaimed).length,
      passes: current.filter(hasPass).length,
      checkedIn: current.filter(isCheckedIn).length,
      teamAssigned: current.filter(
        (registration) => teamForRegistration(registration).assigned,
      ).length,
    };
  }, [registrations]);

  const filteredRegistrations = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return registrations
      .filter((registration) => {
        if (filter === "eligible" && !isCurrentParticipant(registration))
          return false;
        if (filter === "excluded" && isCurrentParticipant(registration))
          return false;
        if (filter === "claimed" && !isClaimed(registration)) return false;
        if (
          filter === "awaiting-account" &&
          (!hasInvitation(registration) || isClaimed(registration))
        )
          return false;
        if (filter === "not-invited" && hasInvitation(registration))
          return false;
        if (
          filter === "invitation-failed" &&
          invitationFor(registration)?.status !== "failed"
        )
          return false;
        if (filter === "pass" && !hasPass(registration)) return false;
        if (filter === "no-pass" && hasPass(registration)) return false;
        if (filter === "checked-in" && !isCheckedIn(registration)) return false;
        if (filter === "not-checked-in" && isCheckedIn(registration))
          return false;
        if (
          filter === "team-assigned" &&
          !teamForRegistration(registration).assigned
        )
          return false;
        if (
          filter === "team-unassigned" &&
          teamForRegistration(registration).assigned
        )
          return false;
        if (!normalizedQuery) return true;
        const searchable =
          `${fullNameFor(registration)} ${JSON.stringify(registration)}`.toLowerCase();
        return normalizedQuery
          .split(/\s+/)
          .every((word) => searchable.includes(word));
      })
      .sort((a, b) => fullNameFor(a).localeCompare(fullNameFor(b)));
  }, [filter, query, registrations]);

  return (
    <main className="dq-admin-page">
      <a className="dq-skip-link" href="#attendee-table">
        Skip to attendee table
      </a>
      <div className="dq-circuit" aria-hidden="true" />

      <header className="dq-header">
        <Link
          className="dq-brand"
          to="/events/duquantum-2026"
          aria-label="DuQuantum attendee portal"
        >
          <img src="/duquantum-2026/logo.svg" alt="DuQuantum" />
          <span>ADMIN // ATTENDEES</span>
        </Link>
        <nav className="dq-header-actions" aria-label="Admin navigation">
          <Link to="/admin/events/duquantum-2026/check-in">Scanner</Link>
          <Link to="/admin/roles">Staff access</Link>
          <Link to="/events/duquantum-2026">Participant view</Link>
          <button
            type="button"
            onClick={() =>
              logout({ logoutParams: { returnTo: window.location.origin } })
            }
          >
            Log out
          </button>
        </nav>
      </header>

      <section className="dq-admin-shell" aria-labelledby="dq-admin-title">
        <div className="dq-admin-title-row">
          <div>
            <p className="dq-eyebrow">DUQUANTUM 2026 // PRIVATE OPERATIONS</p>
            <h1 id="dq-admin-title">Attendee manifest</h1>
            <p>
              Confirmation data, portal claims, issued passes, and check-in
              progress in one view.
            </p>
          </div>
          <button
            className="dq-secondary-button"
            type="button"
            onClick={loadRegistrations}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh data"}
          </button>
        </div>
        {checkInMessage && (
          <p role="status" className="dq-help-copy">
            {checkInMessage}
          </p>
        )}

        <div className="dq-privacy-note" role="note">
          <strong>Private attendee data.</strong> Use this view only for
          DuQuantum operations. Do not copy phone numbers or consent responses
          into unsecured documents.
        </div>

        {error && (
          <div className="dq-alert dq-alert-error" role="alert">
            {error}
          </div>
        )}

        <section className="dq-admin-stats" aria-label="Attendee totals">
          <article>
            <span>Current participants</span>
            <strong>{stats.total}</strong>
          </article>
          <article>
            <span>Invitations sent</span>
            <strong>{stats.invited}</strong>
          </article>
          <article>
            <span>Accounts completed</span>
            <strong>{stats.claimed}</strong>
          </article>
          <article>
            <span>Passes issued</span>
            <strong>{stats.passes}</strong>
          </article>
          <article>
            <span>Checked in</span>
            <strong>{stats.checkedIn}</strong>
          </article>
          <article>
            <span>Team linked</span>
            <strong>{stats.teamAssigned}</strong>
          </article>
        </section>

        <section className="dq-operations-strip" aria-label="Event operations">
          <div>
            <p className="dq-terminal-label">ARRIVAL_PROGRESS // LIVE</p>
            <strong>
              {stats.total
                ? `${Math.round((stats.checkedIn / stats.total) * 100)}% checked in`
                : "Waiting for roster"}
            </strong>
            <div className="dq-progress-track" aria-hidden="true">
              <span
                style={{
                  width: stats.total
                    ? `${(stats.checkedIn / stats.total) * 100}%`
                    : "0%",
                }}
              />
            </div>
          </div>
          <div className="dq-operation-actions">
            <Link
              className="dq-primary-button"
              to="/admin/events/duquantum-2026/check-in"
            >
              Open phone scanner
            </Link>
            <Link className="dq-secondary-button" to="/admin/roles">
              Manage staff access
            </Link>
          </div>
        </section>

        <DuQuantumTeamDirectory
          teams={teams}
          loading={teamsLoading}
          error={teamsError}
        />

        <section
          className="dq-manifest-panel"
          aria-labelledby="manifest-heading"
        >
          <div className="dq-manifest-toolbar">
            <div>
              <p className="dq-terminal-label">
                MANIFEST // {filteredRegistrations.length} RECORDS
              </p>
              <h2 id="manifest-heading">Confirmation responses</h2>
            </div>
            <div className="dq-manifest-controls">
              <label>
                <span>Search attendees</span>
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Name, email, school, team…"
                />
              </label>
              <label>
                <span>Filter status</span>
                <select
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                >
                  <option value="eligible">Current participants</option>
                  <option value="all">All stored records</option>
                  <option value="excluded">Excluded / archived</option>
                  <option value="claimed">Account completed</option>
                  <option value="awaiting-account">
                    Invited, not completed
                  </option>
                  <option value="not-invited">Invitation not sent</option>
                  <option value="invitation-failed">Invitation failed</option>
                  <option value="pass">Pass issued</option>
                  <option value="no-pass">Pass not issued</option>
                  <option value="checked-in">Checked in</option>
                  <option value="not-checked-in">Not checked in</option>
                  <option value="team-assigned">Team assigned</option>
                  <option value="team-unassigned">No team assignment</option>
                </select>
              </label>
              {(query || filter !== "eligible") && (
                <button
                  className="dq-clear-filters"
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setFilter("eligible");
                  }}
                >
                  Clear filters
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div className="dq-admin-loading" role="status">
              Loading attendee records…
            </div>
          ) : filteredRegistrations.length ? (
            <div className="dq-table-scroll" id="attendee-table" tabIndex="0">
              <table className="dq-attendee-table">
                <caption className="dq-visually-hidden">
                  DuQuantum 2026 confirmed attendees
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Attendee</th>
                    <th scope="col">University / program</th>
                    <th scope="col">Team / track</th>
                    <th scope="col">Account</th>
                    <th scope="col">Pass</th>
                    <th scope="col">Check-in</th>
                    <th scope="col">Submitted</th>
                    <th scope="col">
                      <span className="dq-visually-hidden">Details</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRegistrations.map((registration, index) => {
                    const key = registrationKey(registration, index);
                    const isOpen = expanded === key;
                    const passId = passIdFor(registration);
                    const passState = passStateFor(registration);
                    const checkIns = checkInsFor(registration);
                    const invitation = invitationFor(registration);
                    const deliveries = emailDeliveriesFor(registration);
                    const sourceData = flattenObject(
                      sourceDataFor(registration),
                    );
                    const team = teamForRegistration(registration);
                    return (
                      <React.Fragment key={key}>
                        <tr className={isOpen ? "is-expanded" : ""}>
                          <td>
                            <strong>{fullNameFor(registration)}</strong>
                            <span>
                              {formatValue(
                                readField(registration, [
                                  "email",
                                  "email_address",
                                  "email address",
                                ]),
                              )}
                            </span>
                          </td>
                          <td>
                            <strong>
                              {formatValue(
                                readField(registration, [
                                  "university",
                                  "school",
                                  "institution",
                                ]),
                              )}
                            </strong>
                            <span>
                              {formatValue(
                                readField(registration, [
                                  "degree_program",
                                  "degree",
                                  "program",
                                ]),
                              )}
                            </span>
                          </td>
                          <td>
                            <strong>{teamLabel(team)}</strong>
                            <span>
                              {team.track
                                ? `Track: ${team.track}`
                                : team.trackPreference
                                  ? `Prefers: ${team.trackPreference}`
                                  : "Track: N/A"}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`dq-admin-chip ${
                                isClaimed(registration)
                                  ? "success"
                                  : invitation?.status === "sent"
                                    ? "pending"
                                    : "warning"
                              }`}
                            >
                              {isClaimed(registration)
                                ? "Connected"
                                : invitationLabel(invitation)}
                            </span>
                            {invitation?.sent_at && (
                              <small>
                                {formatDateTime(invitation.sent_at)}
                              </small>
                            )}
                          </td>
                          <td>
                            <span
                              className={`dq-admin-chip ${passState ? "success" : "neutral"}`}
                            >
                              {passState ? formatValue(passState) : "Pending"}
                            </span>
                            {passId && (
                              <small>…{String(passId).slice(-8)}</small>
                            )}
                          </td>
                          <td>
                            <span
                              className={`dq-admin-chip ${isCheckedIn(registration) ? "success" : "neutral"}`}
                            >
                              {isCheckedIn(registration)
                                ? `Checked in${checkIns.length > 1 ? ` ×${checkIns.length}` : ""}`
                                : "Not yet"}
                            </span>
                            {!isCheckedIn(registration) &&
                              (checkInTarget?.id === registration.id ? (
                                <div
                                  className="dq-arrival-confirm"
                                  role="group"
                                  aria-label={`Confirm arrival for ${fullNameFor(registration)}`}
                                >
                                  <p>
                                    Verify this attendee's name and email before
                                    confirming arrival.
                                  </p>
                                  <button
                                    type="button"
                                    className="dq-secondary-button"
                                    onClick={confirmArrival}
                                    disabled={checkingIn}
                                  >
                                    {checkingIn
                                      ? "Checking in…"
                                      : "Confirm arrival check-in"}
                                  </button>
                                  <button
                                    type="button"
                                    className="dq-inline-operation"
                                    onClick={() => setCheckInTarget(null)}
                                    disabled={checkingIn}
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  type="button"
                                  className="dq-inline-operation"
                                  aria-label={`Check in ${fullNameFor(registration)}`}
                                  disabled={
                                    checkingIn ||
                                    !isCurrentParticipant(registration) ||
                                    (passState && passState !== "active")
                                  }
                                  onClick={() => {
                                    setCheckInTarget(registration);
                                    setCheckInMessage("");
                                  }}
                                >
                                  Check in
                                </button>
                              ))}
                          </td>
                          <td>
                            {formatDateTime(
                              readField(registration, [
                                "timestamp",
                                "submitted_at",
                                "source_timestamp",
                                "created_at",
                              ]),
                            )}
                          </td>
                          <td>
                            <button
                              className="dq-detail-button"
                              type="button"
                              aria-expanded={isOpen}
                              aria-controls={`details-${key}`}
                              onClick={() => setExpanded(isOpen ? null : key)}
                            >
                              {isOpen ? "Close" : "View"}
                              <span aria-hidden="true">
                                {isOpen ? "−" : "+"}
                              </span>
                            </button>
                          </td>
                        </tr>
                        {isOpen && (
                          <tr className="dq-detail-row">
                            <td colSpan="8" id={`details-${key}`}>
                              <div className="dq-record-details">
                                {FIELD_GROUPS.map((group) => (
                                  <section key={group.title}>
                                    <h3>{group.title}</h3>
                                    <dl>
                                      {group.fields.map((field) => (
                                        <div key={field.label}>
                                          <dt>{field.label}</dt>
                                          <dd>
                                            {formatValue(
                                              readField(
                                                registration,
                                                field.keys,
                                              ),
                                            )}
                                          </dd>
                                        </div>
                                      ))}
                                    </dl>
                                  </section>
                                ))}

                                <section className="dq-admin-team-details">
                                  <h3>Team &amp; challenge</h3>
                                  <dl>
                                    <div>
                                      <dt>Team</dt>
                                      <dd>{teamLabel(team)}</dd>
                                    </div>
                                    <div>
                                      <dt>Assigned track</dt>
                                      <dd>{formatTeamValue(team.track)}</dd>
                                    </div>
                                    <div>
                                      <dt>Track preference</dt>
                                      <dd>
                                        {formatTeamValue(team.trackPreference)}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Assigned challenge</dt>
                                      <dd>{formatTeamValue(team.challenge)}</dd>
                                    </div>
                                    <div>
                                      <dt>Challenge preferences</dt>
                                      <dd>
                                        {formatTeamValue(
                                          team.challengePreferences,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Sponsor</dt>
                                      <dd>{formatTeamValue(team.sponsor)}</dd>
                                    </div>
                                    <div>
                                      <dt>Sponsor contact</dt>
                                      <dd>
                                        {team.sponsorContactEmail ? (
                                          <>
                                            {team.sponsorContactName && (
                                              <span>
                                                {team.sponsorContactName}
                                              </span>
                                            )}
                                            <a
                                              href={`mailto:${team.sponsorContactEmail}`}
                                            >
                                              {team.sponsorContactEmail}
                                            </a>
                                          </>
                                        ) : (
                                          formatTeamValue(
                                            team.sponsorContactName,
                                          )
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Requested additional teammates</dt>
                                      <dd>
                                        {formatTeamValue(
                                          team.requestedAdditionalTeammates,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>
                                        Additional teammate request details
                                      </dt>
                                      <dd>
                                        {formatTeamValue(
                                          team.additionalTeammatesDetail,
                                        )}
                                      </dd>
                                    </div>
                                  </dl>
                                  <h4>Teammates</h4>
                                  {team.teammates.length ? (
                                    <ul className="dq-admin-team-members">
                                      {team.teammates.map(
                                        (member, memberIndex) => (
                                          <li
                                            key={`${member.name}-${memberIndex}`}
                                          >
                                            <strong>{member.name}</strong>
                                            {member.email && (
                                              <a
                                                href={`mailto:${member.email}`}
                                              >
                                                {member.email}
                                              </a>
                                            )}
                                            {member.discordUsername && (
                                              <span>
                                                Discord:{" "}
                                                {member.discordUsername}
                                              </span>
                                            )}
                                            {member.matchMethod && (
                                              <small>
                                                Match: {member.matchMethod}
                                              </small>
                                            )}
                                          </li>
                                        ),
                                      )}
                                    </ul>
                                  ) : (
                                    <p>N/A</p>
                                  )}
                                </section>

                                <section className="dq-source-responses">
                                  <h3>Original imported responses</h3>
                                  {Object.keys(sourceData).length ? (
                                    <dl>
                                      {Object.entries(sourceData).map(
                                        ([label, value]) => (
                                          <div key={label}>
                                            <dt>{label}</dt>
                                            <dd>{formatValue(value)}</dd>
                                          </div>
                                        ),
                                      )}
                                    </dl>
                                  ) : (
                                    <p>
                                      No additional source fields were stored
                                      for this record.
                                    </p>
                                  )}
                                </section>

                                <section>
                                  <h3>Portal operations</h3>
                                  <dl>
                                    <div>
                                      <dt>Registration ID</dt>
                                      <dd>
                                        {formatValue(
                                          registration.id ||
                                            registration.registration_id,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Claimed at</dt>
                                      <dd>
                                        {formatDateTime(
                                          registration.claimed_at,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Admission status</dt>
                                      <dd>
                                        {formatValue(
                                          registration.admission_status ||
                                            registration.status,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>RSVP status</dt>
                                      <dd>
                                        {formatValue(
                                          registration.rsvp_status ||
                                            registration.attendance_status,
                                        )}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Pass state</dt>
                                      <dd>{formatValue(passState)}</dd>
                                    </div>
                                    <div>
                                      <dt>Check-in records</dt>
                                      <dd>
                                        {checkIns.length ||
                                          (isCheckedIn(registration) ? 1 : 0)}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Invitation status</dt>
                                      <dd>
                                        {invitation
                                          ? `${invitationLabel(invitation)} ${formatDateTime(invitation.sent_at || invitation.created_at)}`
                                          : "Not sent"}
                                      </dd>
                                    </div>
                                  </dl>
                                  <Link
                                    className="dq-inline-operation"
                                    to="/admin/events/duquantum-2026/check-in"
                                  >
                                    Open check-in scanner
                                  </Link>
                                </section>
                                <section className="dq-delivery-history">
                                  <h3>Email delivery history</h3>
                                  {deliveries.length ? (
                                    <ol>
                                      {deliveries.map((delivery) => (
                                        <li key={delivery.id}>
                                          <strong>
                                            {humanizeCampaign(
                                              delivery.campaign_key,
                                            )}
                                          </strong>
                                          <span>{delivery.status}</span>
                                          <time
                                            dateTime={
                                              delivery.sent_at ||
                                              delivery.created_at
                                            }
                                          >
                                            {formatDateTime(
                                              delivery.sent_at ||
                                                delivery.created_at,
                                            )}
                                          </time>
                                        </li>
                                      ))}
                                    </ol>
                                  ) : (
                                    <p>No portal emails recorded.</p>
                                  )}
                                </section>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="dq-empty-results">
              <h3>No attendee records match this view.</h3>
              <p>
                {registrations.length
                  ? "Clear the search or choose another status filter."
                  : "The confirmation import has not produced any attendee records yet."}
              </p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
};

export default DuQuantumAdminPage;

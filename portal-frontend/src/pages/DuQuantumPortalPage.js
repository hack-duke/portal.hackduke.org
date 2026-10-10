import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { Link } from "react-router-dom";
import axios from "axios";
import { QRCodeSVG } from "qrcode.react";
import { createGetAuthToken } from "../utils/authUtils";
import DuQuantumCommunityCard from "../components/DuQuantumCommunityCard";
import DuQuantumMobileCompanion from "../components/DuQuantumMobileCompanion";
import DuQuantumSchedule from "../components/DuQuantumSchedule";
import "./DuQuantumPortal.css";

const EVENT_SLUG = "duquantum-2026";
const FALLBACK_EVENT = {
  name: "DuQuantum 2026",
  start_at: "2026-10-24T09:00:00-04:00",
  end_at: "2026-10-25T18:00:00-04:00",
};

const unpackEventResponse = (payload) => payload?.data || payload || {};

const findEvent = (payload) => {
  const events = Array.isArray(payload)
    ? payload
    : payload?.events || payload?.items || [];
  return events.find((event) => event.slug === EVENT_SLUG) || null;
};

const formatDateRange = (event) => {
  const start = new Date(event?.start_at || FALLBACK_EVENT.start_at);
  const end = new Date(event?.end_at || FALLBACK_EVENT.end_at);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return "October 24–25, 2026";
  }

  const startText = new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "America/New_York",
  }).format(start);
  const endText = new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "America/New_York",
  }).format(end);
  return `${startText}–${endText}`;
};

const humanize = (value) => {
  if (!value) return "Not recorded";
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
};

const formatRegistrationValue = (value) => {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (value === null || value === undefined || value === "") {
    return "Not provided";
  }
  return String(value);
};

const CONFIRMATION_FIELDS = [
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone" },
  { key: "age", label: "Age on October 24" },
  { key: "university", label: "University" },
  { key: "degree_program", label: "Degree program / level" },
  { key: "country", label: "Country of residence" },
  { key: "attendance_commitment", label: "Attendance commitment" },
  { key: "photo_release_consent", label: "Photo and recording consent" },
  {
    key: "mlh_code_of_conduct_consent",
    label: "MLH Code of Conduct agreement",
  },
  { key: "mlh_privacy_policy_consent", label: "MLH Privacy Policy agreement" },
  { key: "data_sharing_consent", label: "MLH data-sharing agreement" },
  { key: "mlh_marketing_opt_in", label: "MLH + DEV updates" },
];

const DuQuantumPortalPage = () => {
  const { getAccessTokenSilently, logout, user } = useAuth0();
  const [event, setEvent] = useState(FALLBACK_EVENT);
  const [registration, setRegistration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState("");
  const [needsClaim, setNeedsClaim] = useState(false);

  const loadPortal = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      const headers = { Authorization: `Bearer ${token}` };
      const [eventsResult, registrationResult] = await Promise.allSettled([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/events`, { headers }),
        axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/me`,
          { headers },
        ),
      ]);

      if (eventsResult.status === "fulfilled") {
        setEvent(findEvent(eventsResult.value.data) || FALLBACK_EVENT);
      }

      if (registrationResult.status === "fulfilled") {
        const payload = unpackEventResponse(registrationResult.value.data);
        if (payload.event) setEvent(payload.event);
        setRegistration(payload.registration || null);
        setNeedsClaim(Boolean(payload.claim_required || !payload.registration));
      } else {
        const status = registrationResult.reason?.response?.status;
        if (status === 404 || status === 409) {
          setRegistration(null);
          setNeedsClaim(true);
        } else if (status === 403) {
          setError(
            registrationResult.reason?.response?.data?.detail ||
              "Your email must be verified before you can access an attendee pass.",
          );
        } else {
          setError(
            registrationResult.reason?.response?.data?.detail ||
              "We could not load your DuQuantum registration. Please try again.",
          );
        }
      }
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          "We could not load the DuQuantum portal. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }, [getAccessTokenSilently]);

  useEffect(() => {
    loadPortal();
  }, [loadPortal]);

  const claimRegistration = async () => {
    setClaiming(true);
    setError("");
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/claim`,
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const payload = unpackEventResponse(response.data);
      if (payload.event) setEvent(payload.event);
      setRegistration(payload.registration || null);
      setNeedsClaim(Boolean(payload.claim_required || !payload.registration));
    } catch (claimError) {
      setError(
        claimError?.response?.data?.detail ||
          "No confirmation response matched your verified login email. Contact the organizers if you used another email.",
      );
    } finally {
      setClaiming(false);
    }
  };

  const pass = registration?.pass || registration?.event_pass || null;
  const publicPassId = pass?.public_id || registration?.pass_public_id || null;
  const passActive =
    publicPassId &&
    !["revoked", "inactive"].includes(pass?.state?.toLowerCase());
  const attendeeName = useMemo(() => {
    const name = [registration?.first_name, registration?.last_name]
      .filter(Boolean)
      .join(" ");
    return name || registration?.preferred_name || user?.name || "Attendee";
  }, [registration, user]);

  return (
    <main className="dq-page">
      <a className="dq-skip-link" href="#dq-main-content">
        Skip to attendee pass
      </a>
      <div className="dq-circuit" aria-hidden="true" />

      <header className="dq-header">
        <Link
          className="dq-brand"
          to="/events/duquantum-2026"
          aria-label="DuQuantum attendee portal"
        >
          <img src="/duquantum-2026/logo.svg" alt="DuQuantum" />
          <span>ATTENDEE PORTAL</span>
        </Link>
        <nav className="dq-header-actions" aria-label="Portal navigation">
          <a href="#duquantum-schedule">Schedule</a>
          <a
            href="https://discord.gg/mqQNBDXkd"
            target="_blank"
            rel="noopener noreferrer"
          >
            Discord
          </a>
          <a href="https://duquantum.org/" target="_blank" rel="noreferrer">
            Event site
          </a>
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

      <section className="dq-hero" aria-labelledby="dq-portal-title">
        <div>
          <p className="dq-eyebrow">DUKE'S QUANTUM COMPUTING HACKATHON</p>
          <h1 id="dq-portal-title">Your event command center</h1>
          <p className="dq-hero-copy">
            Access your arrival pass and review the confirmation attached to
            your verified account.
          </p>
        </div>
        <dl className="dq-event-meta">
          <div>
            <dt>Date</dt>
            <dd>{formatDateRange(event)}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>Wilkinson Building · Duke University</dd>
          </div>
          <div>
            <dt>Check-in</dt>
            <dd>Saturday · 9:00–11:00 AM</dd>
          </div>
        </dl>
      </section>

      <section className="dq-dashboard" id="dq-main-content" aria-live="polite">
        {loading ? (
          <div className="dq-panel dq-loading" role="status">
            <span className="dq-loader" aria-hidden="true" />
            <p>Synchronizing your registration…</p>
          </div>
        ) : (
          <>
            {error && (
              <div className="dq-alert dq-alert-error" role="alert">
                <strong>We hit a snag.</strong>
                <span>{error}</span>
              </div>
            )}

            {needsClaim && !registration ? (
              <article className="dq-panel dq-claim-card">
                <p className="dq-terminal-label">
                  REGISTRATION_LINK // PENDING
                </p>
                <h2>Connect your attendance confirmation</h2>
                <p>
                  You are signed in as <strong>{user?.email}</strong>. We will
                  securely match that verified address to the confirmation
                  list—no form needs to be completed again.
                </p>
                <button
                  className="dq-primary-button"
                  type="button"
                  onClick={claimRegistration}
                  disabled={claiming}
                >
                  {claiming ? "Connecting…" : "Connect my registration"}
                </button>
                <p className="dq-help-copy">
                  Used a different email? Contact{" "}
                  <a href="mailto:organizers@duquantum.org">
                    organizers@duquantum.org
                  </a>
                  .
                </p>
              </article>
            ) : registration ? (
              <div className="dq-content-grid">
                <article className="dq-panel dq-pass-card">
                  <div className="dq-pass-heading">
                    <div>
                      <p className="dq-terminal-label">
                        ACCESS_PASS //{" "}
                        {passActive ? "ACTIVE" : "AWAITING_ISSUE"}
                      </p>
                      <h2>{attendeeName}</h2>
                      <p>{registration.email || user?.email}</p>
                    </div>
                    <span
                      className={`dq-status-chip ${passActive ? "is-active" : "is-pending"}`}
                    >
                      {passActive ? "Ready to scan" : "Pass pending"}
                    </span>
                  </div>

                  {passActive ? (
                    <div className="dq-qr-wrap">
                      <div className="dq-qr-code">
                        <QRCodeSVG
                          value={String(publicPassId)}
                          size={248}
                          level="M"
                          marginSize={2}
                          title={`DuQuantum arrival pass for ${attendeeName}`}
                        />
                      </div>
                      <div className="dq-pass-instructions">
                        <h3>Arrival instructions</h3>
                        <ol>
                          <li>
                            Have this page open before entering the check-in
                            line.
                          </li>
                          <li>Turn up your screen brightness.</li>
                          <li>Present the QR code to event staff.</li>
                        </ol>
                        <p className="dq-pass-reference">
                          PASS REF ·{" "}
                          {String(publicPassId).slice(-8).toUpperCase()}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="dq-pass-pending">
                      <span aria-hidden="true">⌁</span>
                      <div>
                        <h3>Your registration is connected.</h3>
                        <p>
                          The organizers have not issued an active pass for this
                          registration yet.
                        </p>
                      </div>
                    </div>
                  )}
                </article>

                <aside
                  className="dq-side-stack"
                  aria-label="Registration details"
                >
                  <article className="dq-panel dq-status-card">
                    <p className="dq-terminal-label">
                      CONFIRMATION // RECEIVED
                    </p>
                    <h2>Registration status</h2>
                    <dl>
                      <div>
                        <dt>Attendance</dt>
                        <dd>
                          {humanize(
                            registration.rsvp_status ||
                              registration.attendance_status ||
                              "confirmed",
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Admission</dt>
                        <dd>
                          {humanize(
                            registration.admission_status ||
                              registration.status ||
                              "accepted",
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Account</dt>
                        <dd>Connected</dd>
                      </div>
                    </dl>
                  </article>
                  <DuQuantumCommunityCard />
                  <article className="dq-panel dq-support-card">
                    <p className="dq-terminal-label">SUPPORT_CHANNEL // OPEN</p>
                    <h2>Need help?</h2>
                    <p>
                      Questions about your confirmation, pass, or event access
                      are handled by the DuQuantum organizers.
                    </p>
                    <a
                      className="dq-text-link"
                      href="mailto:organizers@duquantum.org"
                    >
                      organizers@duquantum.org <span aria-hidden="true">→</span>
                    </a>
                  </article>
                </aside>
              </div>
            ) : (
              <article className="dq-panel dq-empty-card">
                <h2>No registration is connected</h2>
                <p>
                  Try refreshing the portal or contact the organizers for help.
                </p>
                <button
                  className="dq-secondary-button"
                  type="button"
                  onClick={loadPortal}
                >
                  Refresh portal
                </button>
              </article>
            )}
            {registration && (
              <details className="dq-confirmation-drawer">
                <summary>
                  <span className="dq-menu-mark" aria-hidden="true">
                    <i />
                    <i />
                    <i />
                  </span>
                  <span>
                    <strong>Your confirmation information</strong>
                    <small>
                      Review the details imported from your response
                    </small>
                  </span>
                  <span className="dq-drawer-toggle" aria-hidden="true">
                    +
                  </span>
                </summary>
                <div className="dq-confirmation-content">
                  <p>
                    These details are private and visible only from your
                    signed-in portal. Contact the organizers if anything needs
                    correction.
                  </p>
                  <dl>
                    {CONFIRMATION_FIELDS.map((field) => (
                      <div key={field.key}>
                        <dt>{field.label}</dt>
                        <dd>
                          {formatRegistrationValue(registration[field.key])}
                        </dd>
                      </div>
                    ))}
                  </dl>
                  <a href="mailto:organizers@duquantum.org?subject=DuQuantum%20confirmation%20correction">
                    Request a correction
                  </a>
                </div>
              </details>
            )}
            {registration && passActive && (
              <>
                <DuQuantumSchedule />
                <DuQuantumMobileCompanion
                  getAccessTokenSilently={getAccessTokenSilently}
                />
              </>
            )}
          </>
        )}
      </section>

      <footer className="dq-footer">
        <span>DUQUANTUM 2026 // OCT 24–25</span>
        <span>Hosted by DuQIS × HackDuke</span>
      </footer>
    </main>
  );
};

export default DuQuantumPortalPage;

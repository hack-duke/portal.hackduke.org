import React, { useEffect, useMemo, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { formatDistanceToNow, format } from "date-fns";
import { useWindowSize } from "react-use";
import Confetti from "react-confetti";
import { useLocation, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import axios from "axios";
import classNames from "classnames";
import { PortalLayout } from "../components/portal/PortalLayout";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import {
  ClockIcon,
  PartyIcon,
  CheckCircleIcon,
  HeartIcon,
  FileIcon,
  ExternalIcon,
} from "../components/portal/icons";
import { CURRENT_FORM_KEY, getFormByKey } from "../forms/forms";
import { getFormSections } from "../forms/formSections";
import { createGetAuthToken } from "../utils/authUtils";
import "./ApplicationStatusPage.css";

// Used when the page is opened directly without a ?formKey= query param.
const DEFAULT_FORM_KEY = CURRENT_FORM_KEY;

const STATUS_DISPLAY = {
  pending: {
    label: "Under Review",
    icon: ClockIcon,
    message:
      "Thanks for applying! Our team is reviewing applications, and we'll email you as soon as decisions are out.",
  },
  accepted: {
    label: "Accepted",
    icon: PartyIcon,
    message:
      "Congratulations, you're in! Keep an eye on your email for instructions to confirm your spot.",
  },
  confirmed: {
    label: "Confirmed",
    icon: CheckCircleIcon,
    message: "You're all set! Show the QR code below at check-in on event day.",
  },
  rejected: {
    label: "Not Selected",
    icon: HeartIcon,
    message:
      "Thank you so much for applying. Unfortunately, we weren't able to offer you a spot this year, and we hope you'll apply again!",
  },
};

const prettifyKey = (key) =>
  key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

const isBlank = (value) =>
  value === null ||
  value === undefined ||
  value === "" ||
  (Array.isArray(value) && value.length === 0);

const displayValue = (value) => {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
};

// For forms without a definition in the frontend (older years), guess layout.
const fallbackSections = (formData) => [
  {
    title: "Your Responses",
    questions: Object.entries(formData).map(([name, value]) => ({
      name,
      label: prettifyKey(name),
      kind:
        typeof value === "boolean"
          ? "check"
          : name === "resume"
            ? "file"
            : typeof value === "string" && value.length > 100
              ? "long"
              : "short",
    })),
  },
];

const ResumeCard = ({ fileKey, url, label }) => {
  const fileName = String(fileKey).split("/").pop();
  return (
    <div className="resume-card">
      <div className="resume-card-header">
        <span className="resume-icon" aria-hidden="true">
          <FileIcon />
        </span>
        <div className="resume-meta">
          <span className="resume-label">{label}</span>
          <span className="resume-name">{fileName}</span>
        </div>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="resume-open"
          >
            Open <ExternalIcon />
          </a>
        )}
      </div>
      {url ? (
        <iframe
          className="resume-preview"
          src={`${url}#view=FitH`}
          title={`Resume preview: ${fileName}`}
        />
      ) : (
        <p className="resume-unavailable">
          A preview isn't available right now. Refresh the page to try again.
        </p>
      )}
    </div>
  );
};

const AnswerSection = ({ section, formData, resumeUrl }) => {
  const answered = section.questions.filter((q) => !isBlank(formData[q.name]));
  if (answered.length === 0) return null;

  const short = answered.filter((q) => q.kind === "short");
  const long = answered.filter((q) => q.kind === "long");
  const files = answered.filter((q) => q.kind === "file");
  const checks = answered.filter((q) => q.kind === "check");

  return (
    <section className="answers-card">
      <h2 className="answers-title">{section.title}</h2>

      {short.length > 0 && (
        <dl className="answers-grid">
          {short.map((q) => (
            <div key={q.name} className="answer-item">
              <dt>{q.label}</dt>
              <dd>{displayValue(formData[q.name])}</dd>
            </div>
          ))}
        </dl>
      )}

      {files.map((q) => (
        <ResumeCard
          key={q.name}
          fileKey={formData[q.name]}
          url={resumeUrl}
          label={q.label}
        />
      ))}

      {long.length > 0 && (
        <div className="long-answers">
          {long.map((q) => (
            <div key={q.name} className="long-answer">
              <h3 className="long-answer-question">{q.label}</h3>
              <p className="long-answer-text">
                {displayValue(formData[q.name])}
              </p>
            </div>
          ))}
        </div>
      )}

      {checks.length > 0 && (
        <ul className="agreements-list">
          {checks.map((q) => (
            <li key={q.name} className="agreement-item">
              <span
                className={classNames("agreement-mark", {
                  "agreement-mark-no": !formData[q.name],
                })}
                aria-hidden="true"
              >
                {formData[q.name] ? "✓" : "–"}
              </span>
              <span>{q.label}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

const ApplicationStatusPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const { width, height } = useWindowSize();
  const location = useLocation();
  const navigate = useNavigate();
  const { firstTime } = location.state || {};

  const searchParams = new URLSearchParams(location.search);
  const formKey = searchParams.get("formKey") || DEFAULT_FORM_KEY;
  const formDefinition = getFormByKey(formKey);

  useEffect(() => {
    const fetchApplication = async () => {
      try {
        setLoading(true);
        const getAuthToken = createGetAuthToken(
          getAccessTokenSilently,
          setError,
        );
        const token = await getAuthToken();
        if (!token) {
          return;
        }
        const response = await axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/application`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: { form_key: formKey },
          },
        );
        setApplication(response.data);
      } catch (err) {
        if (err.response?.status === 404) {
          navigate("/application");
        } else {
          setError(
            err.response?.data?.error || "Couldn't load your application.",
          );
        }
      } finally {
        setLoading(false);
      }
    };

    fetchApplication();
  }, [getAccessTokenSilently, navigate, formKey]);

  const formData = useMemo(() => application?.form_data || {}, [application]);
  const sections = useMemo(
    () =>
      formDefinition
        ? getFormSections(formDefinition)
        : fallbackSections(formData),
    [formDefinition, formData],
  );

  const status = application?.status?.toLowerCase();
  const statusInfo = STATUS_DISPLAY[status] || {
    label: application?.status || "",
    icon: ClockIcon,
    message: "",
  };
  const StatusIcon = statusInfo.icon;
  const showQR = status === "accepted" || status === "confirmed";
  const submittedAt = application
    ? new Date(application.created_at + "Z")
    : null;

  return (
    <PortalLayout>
      {loading && <FullPageLoadingSpinner />}
      {firstTime && (
        <div className="confetti">
          <Confetti
            width={width}
            height={height}
            recycle={false}
            numberOfPieces={400}
          />
        </div>
      )}

      <div className="status-page">
        <header className="status-header">
          <p className="status-eyebrow">
            {formDefinition?.title || "Your Application"}
          </p>
          <h1 className="status-page-title">
            {firstTime ? "Application submitted!" : "Your Application"}
          </h1>
        </header>

        {error && <p className="status-error">{error}</p>}

        {application && (
          <>
            <section
              className={classNames("status-hero", `status-hero-${status}`)}
              aria-live="polite"
            >
              <div className="status-hero-main">
                <span className="status-hero-icon" aria-hidden="true">
                  <StatusIcon />
                </span>
                <div>
                  <p className="status-hero-label">Application status</p>
                  <p className="status-hero-value">{statusInfo.label}</p>
                </div>
              </div>
              {statusInfo.message && (
                <p className="status-hero-message">{statusInfo.message}</p>
              )}
              {submittedAt && (
                <p className="status-hero-submitted">
                  Submitted {format(submittedAt, "MMMM d, yyyy 'at' h:mm a")} (
                  {formatDistanceToNow(submittedAt, { addSuffix: true })})
                </p>
              )}

              {showQR && (
                <div className="qr-section">
                  <button
                    type="button"
                    className="qr-code-container"
                    onClick={() => setShowQRModal(true)}
                    aria-label="Enlarge check-in QR code"
                  >
                    <QRCodeSVG
                      value={application.user_id || ""}
                      size={168}
                      marginSize={2}
                      minVersion={6}
                    />
                  </button>
                  <div>
                    <p className="qr-titles">Check-in QR code</p>
                    <p className="qr-instructions">
                      Show this at check-in. Tap to enlarge.
                    </p>
                  </div>
                </div>
              )}
            </section>

            {sections.map((section) => (
              <AnswerSection
                key={section.title}
                section={section}
                formData={formData}
                resumeUrl={application.resume_url}
              />
            ))}

            <p className="status-footer">
              Need to change something? Email{" "}
              <a href="mailto:hackers@hackduke.org">hackers@hackduke.org</a>.
            </p>
          </>
        )}
      </div>

      {showQRModal && application && (
        <div className="qr-modal-overlay" onClick={() => setShowQRModal(false)}>
          <div className="qr-modal-content">
            <QRCodeSVG
              value={application.user_id || ""}
              size={Math.min(width * 0.8, height * 0.8)}
              marginSize={2}
              minVersion={6}
            />
          </div>
        </div>
      )}
    </PortalLayout>
  );
};

export default ApplicationStatusPage;

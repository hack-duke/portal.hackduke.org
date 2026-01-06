import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { createGetAuthToken } from "../utils/authUtils";
import { useAdminLockRelease } from "../hooks/useAdminLockRelease";
import "./AdminJudgePage.css";

const AdminApplicationViewPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const { appId } = useParams();
  const sessionId = location.state?.sessionId;
  const searchQuery = location.state?.searchQuery;
  const statusFilter = location.state?.statusFilter;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [currentApp, setCurrentApp] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [isLockedByOther, setIsLockedByOther] = useState(false);
  const [lockedByEmail, setLockedByEmail] = useState(null);
  const [stats, setStats] = useState(null);

  // Release locks when tab/window is closed (only if session is still valid)
  useAdminLockRelease(sessionId, showTimeoutModal);

  useEffect(() => {
    if (!sessionId) {
      navigate("/admin", { replace: true });
      return;
    }

    if (hasInitialized.current) {
      return;
    }
    hasInitialized.current = true;

    fetchApplication();
    fetchStats();
  }, [sessionId, navigate, appId]);

  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        setShowTimeoutModal(true);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId]);

  const fetchApplication = async () => {
    try {
      setLoading(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/application/${appId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setCurrentApp(response.data);
      setIsLockedByOther(response.data.is_locked_by_other);
      setLockedByEmail(response.data.locked_by_email);
      setError(null);
      setLoading(false);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Application not found.");
      } else if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to load application.");
      }
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/stats`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );
      setStats(response.data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  const submitDecision = async (decision) => {
    if (!currentApp || isLockedByOther) return;

    try {
      setSubmitting(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        setSubmitting(false);
        return;
      }

      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/application/${currentApp.id}/decision`,
        { decision },
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setSubmitting(false);

      // Stay on view and update the displayed status
      const newStatus = decision === "accept" ? "ACCEPTED" : decision === "reject" ? "REJECTED" : "PENDING";
      setCurrentApp((prev) => ({
        ...prev,
        status: newStatus,
      }));
      fetchStats();
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to submit decision.");
      }
      setSubmitting(false);
    }
  };

  const handleBack = async () => {
    // Release the lock before going back
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (token && currentApp && !isLockedByOther) {
        await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/admin/application/${currentApp.id}/release-lock`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
            params: { session_id: sessionId },
          }
        );
      }
    } catch (err) {
      console.error("Error releasing lock:", err);
    }
    navigate("/admin/applicants", { state: { sessionId, searchQuery, statusFilter } });
  };

  const getStatusBadgeClass = (status) => {
    switch (status?.toUpperCase()) {
      case "ACCEPTED":
        return "accepted";
      case "REJECTED":
        return "rejected";
      default:
        return "pending";
    }
  };

  if (loading) {
    return <FullPageLoadingSpinner />;
  }

  if (!sessionId) {
    return <FullPageLoadingSpinner />;
  }

  if (!currentApp) {
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="judge-container judge-empty">
          <h2>Application Not Found</h2>
          <p>{error || "The application could not be loaded."}</p>
          <Button onClick={handleBack} style={{ marginTop: "32px" }}>
            Return to Applicants
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="judge-container">
        <div className="judge-top-bar">
          <button
            className="judge-back-btn"
            onClick={handleBack}
            title="Return to applicants table"
          >
            ← Return to Applicants
          </button>

          {stats && (
            <div className="judge-stats-bar">
              <span className="stat-item pending">
                {stats.total_pending} pending
              </span>
              <span className="stat-item accepted">
                {stats.total_accepted} accepted
              </span>
              <span className="stat-item rejected">
                {stats.total_rejected} rejected
              </span>
              <span className="stat-item yours">
                {(stats.user_accepted || 0) + (stats.user_rejected || 0)} by you
              </span>
            </div>
          )}
        </div>

        <div className="judge-card">
          <div className="judge-header">
            <h1 className="judge-title">Viewing Application</h1>
            <div className="judge-status-badges">
              <span className={`status-badge ${getStatusBadgeClass(currentApp.status)}`}>
                {currentApp.status}
              </span>
            </div>
          </div>

          {error && <div className="judge-error">{error}</div>}

          {isLockedByOther && (
            <div className="lock-warning">
              <svg
                className="lock-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M19 11H5C3.89543 11 3 11.8954 3 13V20C3 21.1046 3.89543 22 5 22H19C20.1046 22 21 21.1046 21 20V13C21 11.8954 20.1046 11 19 11Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>
                Application is currently being judged by {lockedByEmail || "another admin"}.
                You can view but not make changes.
              </span>
            </div>
          )}

          <div
            className={`application-content ${currentApp.resume_url ? "has-resume" : ""}`}
          >
            {/* Left Column: Application Fields */}
            <div className="application-responses">
              {currentApp.submission_json && (
                <div className="application-fields">
                  {/* Applicant Header */}
                  <div className="applicant-header">
                    <h2 className="applicant-name">
                      {currentApp.submission_json.pref_name ||
                        currentApp.submission_json.first_name}{" "}
                      {currentApp.submission_json.last_name}
                    </h2>
                    <div className="applicant-meta">
                      <span>{currentApp.submission_json.email}</span>
                      <span className="meta-divider">•</span>
                      <span>Age {currentApp.submission_json.age}</span>
                      <span className="meta-divider">•</span>
                      <span>{currentApp.submission_json.phone}</span>
                    </div>
                  </div>

                  {/* Education Row */}
                  <div className="education-row">
                    <div className="edu-item">
                      <span className="edu-label">School</span>
                      <span className="edu-value">
                        {currentApp.submission_json.university}
                      </span>
                    </div>
                    <div className="edu-item">
                      <span className="edu-label">Major</span>
                      <span className="edu-value">
                        {currentApp.submission_json.major}
                      </span>
                    </div>
                    <div className="edu-item">
                      <span className="edu-label">Grad</span>
                      <span className="edu-value">
                        {currentApp.submission_json.graduation_year}
                      </span>
                    </div>
                    <div className="edu-item">
                      <span className="edu-label">Location</span>
                      <span className="edu-value">
                        {currentApp.submission_json.country}
                      </span>
                    </div>
                  </div>

                  {/* Essays */}
                  <div className="essays-section">
                    <div className="essay">
                      <label className="essay-label">Why HackDuke?</label>
                      <p className="essay-text">
                        {currentApp.submission_json.why_hackduke}
                      </p>
                    </div>
                    <div className="essay">
                      <label className="essay-label">Why Track?</label>
                      <p className="essay-text">
                        {currentApp.submission_json.why_track}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Resume */}
            {currentApp.resume_url && (
              <div className="resume-column">
                <div className="resume-header">
                  <span className="resume-label">Resume</span>
                  <a
                    href={currentApp.resume_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="resume-new-tab"
                  >
                    Open in new tab ↗
                  </a>
                </div>
                <div className="resume-embed-container">
                  <iframe
                    src={`${currentApp.resume_url}#toolbar=0&navpanes=0`}
                    className="resume-embed"
                    title="Applicant Resume"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="judge-actions">
            <Button
              variant="error"
              onClick={() => submitDecision("reject")}
              disabled={submitting || isLockedByOther}
              className={isLockedByOther ? "disabled-locked" : ""}
            >
              Reject
            </Button>
            <Button
              className={`skip-btn ${isLockedByOther ? "disabled-locked" : ""}`}
              onClick={() => submitDecision("pending")}
              disabled={submitting || isLockedByOther}
            >
              Set to Pending
            </Button>
            <Button
              onClick={() => submitDecision("accept")}
              disabled={submitting || isLockedByOther}
              className={isLockedByOther ? "disabled-locked" : ""}
            >
              Accept
            </Button>
          </div>
        </div>

        <Modal
          isOpen={showTimeoutModal}
          title="Session Ended"
          onClose={() => navigate("/")}
        >
          <p>The admin portal has been opened in another tab or browser.</p>
          <p>Only one active session is allowed at a time.</p>
          <Button onClick={() => navigate("/")} className="modal-button">
            Return to Homepage
          </Button>
        </Modal>
      </div>
    </>
  );
};

export default AdminApplicationViewPage;

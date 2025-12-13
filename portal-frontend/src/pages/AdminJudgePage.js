import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { createGetAuthToken } from "../utils/authUtils";
import { useAdminLockRelease } from "../hooks/useAdminLockRelease";
import "./AdminJudgePage.css";

const AdminJudgePage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [currentApp, setCurrentApp] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [stats, setStats] = useState(null);

  // Release locks when tab/window is closed (only if session is still valid)
  useAdminLockRelease(sessionId, showTimeoutModal);

  useEffect(() => {
    // Redirect if no session
    if (!sessionId) {
      navigate("/admin", { replace: true });
      return;
    }

    // Prevent double execution in React StrictMode
    if (hasInitialized.current) {
      return;
    }
    hasInitialized.current = true;

    fetchNextApplication();
    fetchStats();
  }, [sessionId, navigate]);

  // Listen for session changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        // Another tab got a new session, invalidate this one
        setShowTimeoutModal(true);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId]);

  const fetchNextApplication = async () => {
    try {
      setLoading(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/next-application`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setCurrentApp(response.data);
      setError(null);
      setLoading(false);
    } catch (err) {
      if (err.response?.status === 404) {
        setCurrentApp(null);
        setError("No more pending applications!");
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
    if (!currentApp) return;

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
      // Fetch next application and update stats
      fetchNextApplication();
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

  const handleExit = async () => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (token) {
        await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/admin/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
      }
    } catch (err) {
      console.error("Error logging out:", err);
    }
    navigate("/admin");
  };

  if (loading) {
    return <FullPageLoadingSpinner />;
  }

  // Render loading while redirecting if no session
  if (!sessionId) {
    return <FullPageLoadingSpinner />;
  }

  if (!currentApp) {
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="judge-container judge-empty">
          <h2>All Done!</h2>
          <p>There are no more pending applications to review.</p>
          <Button onClick={handleExit} style={{ marginTop: "32px" }}>
            Back to Dashboard
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
            onClick={handleExit}
            title="Exit judging"
          >
            ← Back
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
            <h1 className="judge-title">Reviewing Application</h1>
            <div className="judge-status-badges">
              <span className="status-badge pending">PENDING</span>
            </div>
          </div>

          {error && <div className="judge-error">{error}</div>}

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
              disabled={submitting}
            >
              Reject
            </Button>
            <Button
              className="skip-btn"
              onClick={() => submitDecision("pending")}
              disabled={submitting}
            >
              Skip (Keep Pending)
            </Button>
            <Button
              onClick={() => submitDecision("accept")}
              disabled={submitting}
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

export default AdminJudgePage;

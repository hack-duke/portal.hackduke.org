import React, { useState, useEffect, useRef, useCallback } from "react";
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
import "./AdminApplicantsPage.css";
import "./AdminDecisionEmailsPage.css";

const AdminDecisionEmailsPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [sampleStatus, setSampleStatus] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);

  useAdminLockRelease(sessionId, showTimeoutModal);

  const authHeaders = useCallback(async () => {
    const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
    const token = await getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }, [getAccessTokenSilently]);

  const handleRequestError = (err, fallback) => {
    if (err.response?.status === 403) {
      setShowTimeoutModal(true);
    } else {
      setError(err.response?.data?.detail || fallback);
    }
  };

  const fetchPreview = useCallback(async () => {
    try {
      setLoading(true);
      const headers = await authHeaders();
      if (!headers) return;
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/decision-emails/preview`,
        { headers, params: { session_id: sessionId } }
      );
      setPreview(response.data);
      setError(null);
    } catch (err) {
      handleRequestError(err, "Failed to load decision email preview.");
    } finally {
      setLoading(false);
    }
  }, [authHeaders, sessionId]);

  useEffect(() => {
    if (!sessionId) {
      navigate("/admin", { replace: true });
      return;
    }
    if (hasInitialized.current) return;
    hasInitialized.current = true;
    fetchPreview();
  }, [sessionId, navigate, fetchPreview]);

  // Listen for session changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        setShowTimeoutModal(true);
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId]);

  const handleSend = async () => {
    setShowConfirm(false);
    setSending(true);
    setResult(null);
    try {
      const headers = await authHeaders();
      if (!headers) return;
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/decision-emails/send`,
        null,
        { headers, params: { session_id: sessionId } }
      );
      setResult(response.data);
      setError(null);
    } catch (err) {
      handleRequestError(err, "Failed to send decision emails.");
    } finally {
      setSending(false);
      fetchPreview();
    }
  };

  if (!sessionId) {
    return <FullPageLoadingSpinner />;
  }

  const counts = preview?.counts || {};
  const total = preview?.total || 0;
  const sample = sampleStatus && preview?.samples?.[sampleStatus];

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="applicants-container">
        <div className="applicants-header">
          <button
            className="back-btn"
            onClick={() => navigate("/admin", { state: { sessionId } })}
          >
            ← Back to Dashboard
          </button>
          <div className="header-card">
            <div className="header-card-content">
              <h1 className="applicants-title">Decision Emails</h1>
              <p className="applicants-count">
                Emails every accepted or rejected applicant who hasn&apos;t been
                emailed yet. Each applicant is emailed at most once.
              </p>
            </div>
          </div>
        </div>

        {error && <div className="applicants-error">{error}</div>}

        {result && (
          <div
            className={`decision-result ${
              result.failed.length ? "decision-result-warn" : ""
            }`}
          >
            <strong>Sent {result.sent} email{result.sent === 1 ? "" : "s"}.</strong>
            {result.failed.length > 0 && (
              <>
                {" "}
                {result.failed.length} failed and will be retried the next time
                you press Send:
                <ul>
                  {result.failed.map((f) => (
                    <li key={f.application_id}>
                      {f.email} ({f.error})
                    </li>
                  ))}
                </ul>
              </>
            )}
            {result.skipped_missing_email > 0 && (
              <div>
                {result.skipped_missing_email} applicant
                {result.skipped_missing_email === 1 ? " has" : "s have"} no
                email address and {result.skipped_missing_email === 1 ? "was" : "were"} skipped.
              </div>
            )}
          </div>
        )}

        {loading && !preview ? (
          <div className="table-loading">Loading...</div>
        ) : (
          preview && (
            <>
              <div className="decision-cards">
                {[
                  ["accepted", "Accepted", "status-accepted"],
                  ["rejected", "Rejected", "status-rejected"],
                ].map(([key, label, cls]) => (
                  <div className="decision-card" key={key}>
                    <span className={`status-badge ${cls}`}>{label}</span>
                    <div className="decision-count">{counts[key] || 0}</div>
                    <div className="decision-count-label">not yet emailed</div>
                    <button
                      className="decision-link"
                      onClick={() =>
                        setSampleStatus(sampleStatus === key ? null : key)
                      }
                    >
                      {sampleStatus === key ? "Hide email" : "Preview email"}
                    </button>
                  </div>
                ))}
                <div className="decision-card">
                  <span className="status-badge status-pending">Done</span>
                  <div className="decision-count">{preview.already_emailed}</div>
                  <div className="decision-count-label">already emailed</div>
                </div>
              </div>

              {preview.missing_email > 0 && (
                <p className="decision-note">
                  {preview.missing_email} decided applicant
                  {preview.missing_email === 1 ? " has" : "s have"} no email
                  address and will be skipped.
                </p>
              )}

              {sample && (
                <div className="decision-sample">
                  <div className="decision-sample-subject">
                    <span>Subject:</span> {sample.subject}
                  </div>
                  <iframe
                    title="Email preview"
                    className="decision-sample-frame"
                    sandbox=""
                    srcDoc={sample.html}
                  />
                </div>
              )}

              <Button
                className="decision-send-btn"
                disabled={total === 0 || sending}
                onClick={() => setShowConfirm(true)}
              >
                {sending
                  ? "Sending… (don't close this tab)"
                  : total === 0
                  ? "Everyone has been emailed"
                  : `Send ${total} decision email${total === 1 ? "" : "s"}`}
              </Button>
            </>
          )
        )}

        <Modal isOpen={showConfirm} onClose={() => setShowConfirm(false)}>
          <h2>Send {total} emails?</h2>
          <p>
            {counts.accepted || 0} acceptance and {counts.rejected || 0}{" "}
            rejection emails will be sent now. This can&apos;t be undone.
          </p>
          <Button onClick={handleSend} className="modal-button">
            Send emails
          </Button>
          <Button
            onClick={() => setShowConfirm(false)}
            className="modal-button"
            variant="secondary"
          >
            Cancel
          </Button>
        </Modal>

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

export default AdminDecisionEmailsPage;

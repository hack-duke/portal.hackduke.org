import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import Modal from "../components/Modal";
import QuestionManager from "../components/QuestionManager";
import { createGetAuthToken } from "../utils/authUtils";
import { useAdminLockRelease } from "../hooks/useAdminLockRelease";
import "./FormEditorPage.css";

const FormEditorPage = () => {
  const { formKey } = useParams();
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [form, setForm] = useState(null);
  const [editingTitle, setEditingTitle] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    closed_message_title: "",
    closed_message_body: "",
  });

  useAdminLockRelease(sessionId, showTimeoutModal);

  useEffect(() => {
    if (!sessionId) {
      navigate("/admin/forms", { replace: true });
      return;
    }

    if (hasInitialized.current) return;
    hasInitialized.current = true;

    fetchForm();

    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        setShowTimeoutModal(true);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId, formKey, navigate]);

  const fetchForm = async () => {
    try {
      setLoading(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      const foundForm = response.data.find((f) => f.form_key === formKey);
      if (foundForm) {
        setForm(foundForm);
        setFormData({
          title: foundForm.title || "",
          closed_message_title: foundForm.closed_message_title || "",
          closed_message_body: foundForm.closed_message_body || "",
        });
      } else {
        setError("Form not found");
      }
      setError(null);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to load form.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFormDetails = async () => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      const response = await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setForm(response.data);
      setEditingTitle(false);
      setError(null);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError(err.response?.data?.detail || "Failed to save form.");
      }
    }
  };

  if (loading) return <FullPageLoadingSpinner />;

  if (!form) {
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="form-editor-container">
          <div className="error-message">Form not found</div>
          <Button onClick={() => navigate("/admin/forms", { state: { sessionId } })}>
            Back to Forms
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="form-editor-container">
        <button
          className="back-btn"
          onClick={() => navigate("/admin/forms", { state: { sessionId } })}
        >
          ← Back to Forms
        </button>

        <div className="form-editor-header">
          <h1>{form.form_key}</h1>
          <span className={`status-badge ${form.is_open ? "open" : "closed"}`}>
            {form.is_open ? "Open" : "Closed"}
          </span>
        </div>

        {error && <div className="error-message">{error}</div>}

        {/* Form Details Section */}
        <div className="form-details-section">
          <h2>Form Details</h2>
          <div className="form-details-content">
            {editingTitle ? (
              <div className="edit-form-details">
                <div className="form-group">
                  <label htmlFor="title">Title</label>
                  <input
                    id="title"
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="closed_message_title">Closed Message Title</label>
                  <input
                    id="closed_message_title"
                    type="text"
                    value={formData.closed_message_title}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        closed_message_title: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="closed_message_body">Closed Message Body</label>
                  <textarea
                    id="closed_message_body"
                    rows="4"
                    value={formData.closed_message_body}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        closed_message_body: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="form-actions">
                  <Button onClick={handleSaveFormDetails}>Save</Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setEditingTitle(false);
                      setFormData({
                        title: form.title || "",
                        closed_message_title: form.closed_message_title || "",
                        closed_message_body: form.closed_message_body || "",
                      });
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="form-details-display">
                <div className="detail-row">
                  <label>Title:</label>
                  <span>{form.title || "Not set"}</span>
                </div>
                <div className="detail-row">
                  <label>Year:</label>
                  <span>{form.year}</span>
                </div>
                <div className="detail-row">
                  <label>Status:</label>
                  <span>{form.is_open ? "Open for submissions" : "Closed"}</span>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => setEditingTitle(true)}
                >
                  Edit Details
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Question Manager Section */}
        <div className="questions-section">
          <h2>Questions</h2>
          <QuestionManager
            formKey={formKey}
            sessionId={sessionId}
            onError={setError}
          />
        </div>
      </div>

      {/* Session Timeout Modal */}
      <Modal
        isOpen={showTimeoutModal}
        title="Session Ended"
        onClose={() => navigate("/admin/forms", { replace: true })}
      >
        <p>Your admin session has been invalidated. Please log in again.</p>
        <Button onClick={() => navigate("/admin/forms", { replace: true })}>
          Back to Forms
        </Button>
      </Modal>
    </>
  );
};

export default FormEditorPage;

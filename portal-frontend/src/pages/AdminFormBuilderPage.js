import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { createGetAuthToken } from "../utils/authUtils";
import { useAdminLockRelease } from "../hooks/useAdminLockRelease";
import "./AdminFormBuilderPage.css";

const AdminFormBuilderPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forms, setForms] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    form_key: "",
    year: new Date().getFullYear(),
    title: "",
  });
  const [formToDelete, setFormToDelete] = useState(null);

  useAdminLockRelease(sessionId, showTimeoutModal);

  // Validate session and fetch forms
  useEffect(() => {
    if (!sessionId) {
      navigate("/admin", { replace: true });
      return;
    }

    if (hasInitialized.current) return;
    hasInitialized.current = true;

    fetchForms();

    // Listen for multi-tab session conflicts
    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        setShowTimeoutModal(true);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId, navigate]);

  const fetchForms = async () => {
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

      setForms(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to load forms.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateForm = async (e) => {
    e.preventDefault();

    if (!createFormData.form_key || !createFormData.title) {
      setError("Form key and title are required.");
      return;
    }

    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms`,
        {
          ...createFormData,
          is_open: false,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setShowCreateModal(false);
      setCreateFormData({
        form_key: "",
        year: new Date().getFullYear(),
        title: "",
      });
      setError(null);
      await fetchForms();
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError(err.response?.data?.detail || "Failed to create form.");
      }
    }
  };

  const handleDeleteForm = async (formKey) => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      await axios.delete(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setFormToDelete(null);
      setError(null);
      await fetchForms();
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError(err.response?.data?.detail || "Failed to delete form.");
      }
    }
  };

  const handleToggleOpen = async (formKey, currentIsOpen) => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) return;

      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}/toggle-open`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setError(null);
      await fetchForms();
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to toggle form status.");
      }
    }
  };

  if (loading) return <FullPageLoadingSpinner />;

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="form-builder-container">
        <div className="form-builder-header">
          <button
            className="back-btn"
            onClick={() => navigate("/admin", { state: { sessionId } })}
          >
            ← Back to Admin
          </button>
          <h1>Form Builder</h1>
          <Button onClick={() => setShowCreateModal(true)} className="create-btn">
            Create New Form
          </Button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {forms.length === 0 ? (
          <div className="empty-state">
            <p>No forms yet. Create your first form to get started.</p>
          </div>
        ) : (
          <div className="forms-table">
            <table>
              <thead>
                <tr>
                  <th>Form Key</th>
                  <th>Title</th>
                  <th>Year</th>
                  <th>Questions</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {forms.map((form) => (
                  <tr key={form.form_key}>
                    <td className="form-key">{form.form_key}</td>
                    <td>{form.title || "-"}</td>
                    <td>{form.year}</td>
                    <td>{form.question_count}</td>
                    <td>
                      <span
                        className={`status-badge ${
                          form.is_open ? "open" : "closed"
                        }`}
                      >
                        {form.is_open ? "Open" : "Closed"}
                      </span>
                    </td>
                    <td className="actions">
                      <Button
                        variant="secondary"
                        onClick={() =>
                          navigate(
                            `/admin/forms/${form.form_key}/edit`,
                            { state: { sessionId } }
                          )
                        }
                      >
                        Edit
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() =>
                          handleToggleOpen(form.form_key, form.is_open)
                        }
                      >
                        {form.is_open ? "Close" : "Open"}
                      </Button>
                      <Button
                        variant="error"
                        onClick={() => setFormToDelete(form.form_key)}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      <Modal
        isOpen={showCreateModal}
        title="Create New Form"
        onClose={() => {
          setShowCreateModal(false);
          setError(null);
        }}
      >
        <form onSubmit={handleCreateForm} className="create-form">
          <div className="form-group">
            <label htmlFor="form_key">Form Key *</label>
            <input
              id="form_key"
              type="text"
              placeholder="e.g., 2027-cfg-application"
              value={createFormData.form_key}
              onChange={(e) =>
                setCreateFormData({
                  ...createFormData,
                  form_key: e.target.value,
                })
              }
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="title">Form Title *</label>
            <input
              id="title"
              type="text"
              placeholder="e.g., HackDuke 2027 Application"
              value={createFormData.title}
              onChange={(e) =>
                setCreateFormData({
                  ...createFormData,
                  title: e.target.value,
                })
              }
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="year">Year *</label>
            <input
              id="year"
              type="number"
              value={createFormData.year}
              onChange={(e) =>
                setCreateFormData({
                  ...createFormData,
                  year: parseInt(e.target.value),
                })
              }
              required
            />
          </div>

          <div className="modal-actions">
            <Button type="submit">Create Form</Button>
            <Button
              variant="secondary"
              onClick={() => {
                setShowCreateModal(false);
                setError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!formToDelete}
        title="Delete Form?"
        onClose={() => setFormToDelete(null)}
      >
        <div className="delete-confirm">
          <p>
            Are you sure you want to delete <strong>{formToDelete}</strong>?
          </p>
          <p className="warning">This action cannot be undone.</p>
          <div className="modal-actions">
            <Button
              variant="error"
              onClick={() => handleDeleteForm(formToDelete)}
            >
              Delete
            </Button>
            <Button variant="secondary" onClick={() => setFormToDelete(null)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Session Timeout Modal */}
      <Modal
        isOpen={showTimeoutModal}
        title="Session Ended"
        onClose={() => navigate("/admin", { replace: true })}
      >
        <p>Your admin session has been invalidated. Please log in again.</p>
        <Button
          onClick={() => navigate("/admin", { replace: true })}
          className="modal-button"
        >
          Back to Admin Login
        </Button>
      </Modal>
    </>
  );
};

export default AdminFormBuilderPage;

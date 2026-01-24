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
import "./AdminApplicantsPage.css";

const AdminApplicantsPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(null);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);

  // Release locks when tab/window is closed (only if session is still valid)
  useAdminLockRelease(sessionId, showTimeoutModal);

  // Filters - restore from navigation state if returning from application view
  const [searchQuery, setSearchQuery] = useState(location.state?.searchQuery || "");
  const [statusFilter, setStatusFilter] = useState(location.state?.statusFilter || "");
  const [debouncedSearch, setDebouncedSearch] = useState(location.state?.searchQuery || "");

  useEffect(() => {
    if (!sessionId) {
      navigate("/admin", { replace: true });
      return;
    }

    if (hasInitialized.current) {
      return;
    }
    hasInitialized.current = true;

    fetchApplications();
  }, [sessionId, navigate]);

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

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Refetch when filters change
  useEffect(() => {
    if (hasInitialized.current) {
      fetchApplications();
    }
  }, [debouncedSearch, statusFilter]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      const params = { session_id: sessionId };
      if (debouncedSearch) params.search = debouncedSearch;
      if (statusFilter) params.status = statusFilter;

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/applications`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params,
        }
      );

      setApplications(response.data.applications);
      setTotal(response.data.total);
      setError(null);
      setLoading(false);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowTimeoutModal(true);
      } else {
        setError("Failed to load applications.");
      }
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate("/admin", { state: { sessionId } });
  };

  const handleViewApplication = (appId) => {
    navigate(`/admin/application/${appId}`, {
      state: { sessionId, searchQuery, statusFilter }
    });
  };

  const getStatusClass = (status) => {
    switch (status.toLowerCase()) {
      case "accepted":
        return "status-accepted";
      case "rejected":
        return "status-rejected";
      case "confirmed":
        return "status-confirmed";
      default:
        return "status-pending";
    }
  };

  if (!sessionId) {
    return <FullPageLoadingSpinner />;
  }

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="applicants-container">
        <div className="applicants-header">
          <button className="back-btn" onClick={handleBack}>
            ← Back to Dashboard
          </button>
          <div className="header-card">
            <div className="header-card-content">
              <h1 className="applicants-title">All Applicants</h1>
              <p className="applicants-count">{total} applicants found</p>
            </div>
          </div>
        </div>

        <div className="filters-bar">
          <div className="search-box">
            <svg
              className="search-icon"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <input
              type="text"
              placeholder="Search by name, email, university..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="filter-select"
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="accepted">Accepted</option>
              <option value="rejected">Rejected</option>
              <option value="confirmed">Confirmed</option>
            </select>
          </div>
        </div>

        {error && <div className="applicants-error">{error}</div>}

        {loading ? (
          <div className="table-loading">Loading applications...</div>
        ) : (
          <div className="table-wrapper">
            <table className="applicants-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>University</th>
                  <th>Major</th>
                  <th>Grad Year</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {applications.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="no-results">
                      No applicants found
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => (
                    <tr
                      key={app.id}
                      onClick={() => handleViewApplication(app.id)}
                      className="clickable-row"
                    >
                      <td className="name-cell">
                        {app.pref_name || app.first_name} {app.last_name}
                      </td>
                      <td className="email-cell">{app.email}</td>
                      <td>{app.university}</td>
                      <td>{app.major}</td>
                      <td className="year-cell">{app.graduation_year}</td>
                      <td>
                        <span className={`status-badge ${getStatusClass(app.status)}`}>
                          {app.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

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

export default AdminApplicantsPage;

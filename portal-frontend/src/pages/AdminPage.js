import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { createGetAuthToken } from "../utils/authUtils";
import { useAdminLockRelease } from "../hooks/useAdminLockRelease";
import "./AdminPage.css";

const AdminPage = () => {
  console.log("AdminPage component rendering...");

  const {
    getAccessTokenSilently,
    isAuthenticated,
    isLoading: authLoading,
  } = useAuth0();
  const navigate = useNavigate();
  const hasInitialized = useRef(false);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [showMultiTabModal, setShowMultiTabModal] = useState(false);

  // Release locks when tab/window is closed (only if session is still valid)
  useAdminLockRelease(sessionId, showMultiTabModal);

  console.log("Auth0 state:", {
    authLoading,
    isAuthenticated,
    hasGetAccessTokenSilently: !!getAccessTokenSilently,
  });

  useEffect(() => {
    // Prevent double execution in React StrictMode
    if (hasInitialized.current) {
      console.log("Already initialized, skipping...");
      return;
    }

    // Wait for Auth0 to finish loading
    if (authLoading) {
      console.log("Auth is still loading, waiting...");
      return;
    }

    // Redirect non-authenticated users
    if (!isAuthenticated) {
      console.log("Not authenticated, redirecting to /application");
      navigate("/application", { replace: true });
      return;
    }

    console.log("User is authenticated, proceeding with admin check...");
    hasInitialized.current = true;

    const checkAdminStatus = async () => {
      console.log("Starting checkAdminStatus...");
      try {
        setLoading(true);
        const getAuthToken = createGetAuthToken(
          getAccessTokenSilently,
          setError
        );
        const token = await getAuthToken();
        console.log("Token obtained:", !!token);
        if (!token) {
          console.log("No token, aborting");
          setLoading(false);
          return;
        }

        console.log("Calling /admin/auth/check endpoint...");
        const response = await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/admin/auth/check`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        console.log("Admin check response:", response.data);
        setIsAdmin(response.data.is_admin);
        if (response.data.is_admin && response.data.session_id) {
          console.log(
            "User is admin, setting session ID:",
            response.data.session_id
          );
          setSessionId(response.data.session_id);
          // Store session in localStorage to detect multi-tab
          localStorage.setItem("adminSessionId", response.data.session_id);
          // Fetch initial stats
          await fetchStats(token, response.data.session_id);
          // Start ping interval
          startPingInterval(token, response.data.session_id);
        }
        setLoading(false);
        console.log("Admin check complete");
      } catch (err) {
        console.error("Error checking admin status:", err);
        setError("Failed to load admin panel.");
        setLoading(false);
      }
    };

    checkAdminStatus();
  }, [authLoading, isAuthenticated, navigate, getAccessTokenSilently]);

  // Listen for session changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "adminSessionId" && sessionId && e.newValue !== sessionId) {
        // Another tab got a new session, invalidate this one
        setShowMultiTabModal(true);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [sessionId]);

  const fetchStats = async (token, sid) => {
    try {
      const statsRes = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/stats`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sid },
        }
      );
      setStats(statsRes.data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  const startPingInterval = (token, sid) => {
    // Ping every 5 minutes to detect timeout
    const interval = setInterval(
      async () => {
        try {
          await axios.get(`${process.env.REACT_APP_BACKEND_URL}/admin/ping`, {
            headers: { Authorization: `Bearer ${token}` },
            params: { session_id: sid },
          });
        } catch (err) {
          if (err.response?.status === 403) {
            // Session timed out or invalidated
            setShowMultiTabModal(true);
            clearInterval(interval);
          }
        }
      },
      5 * 60 * 1000
    ); // 5 minutes

    return () => clearInterval(interval);
  };

  const handleStartJudging = () => {
    navigate("/admin/judge", { state: { sessionId } });
  };

  const handleViewApplicants = () => {
    navigate("/admin/applicants", { state: { sessionId } });
  };

  // Show spinner while Auth0 is loading or while we're checking admin status
  if (authLoading || loading) {
    console.log("Still loading, showing spinner...", { authLoading, loading });
    return <FullPageLoadingSpinner />;
  }

  // If not authenticated, the useEffect will handle the redirect
  if (!isAuthenticated) {
    return <FullPageLoadingSpinner />;
  }

  console.log("Render state:", { loading, isAdmin, sessionId });

  if (!isAdmin) {
    console.log("User is not admin, redirecting to /application");
    navigate("/application", { replace: true });
    return null;
  }

  if (!sessionId) {
    console.log("No session ID, showing loading...");
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="admin-container">
          <h1>Loading...</h1>
        </div>
      </>
    );
  }

  console.log("Rendering main admin page...");

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="admin-container">
        <div className="admin-header">
          <h1 className="admin-title">Judging Portal</h1>
          <p className="admin-subtitle">
            Review and judge hackathon applications
          </p>
        </div>

        {error && <div className="admin-error">{error}</div>}

        <div className="admin-stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats?.total_pending || 0}</div>
            <div className="stat-label">Pending Applications</div>
          </div>
          <div className="stat-card">
            <div className="stat-number" style={{ color: "#4CAF50" }}>
              {stats?.total_accepted || 0}
            </div>
            <div className="stat-label">Accepted</div>
          </div>
          <div className="stat-card">
            <div className="stat-number" style={{ color: "#FF5252" }}>
              {stats?.total_rejected || 0}
            </div>
            <div className="stat-label">Rejected</div>
          </div>
          <div className="stat-card">
            <div className="stat-number" style={{ color: "#1031D0" }}>
              {stats?.user_accepted || 0}
            </div>
            <div className="stat-label">Your Decisions</div>
          </div>
        </div>

        <div className="admin-actions">
          <Button
            onClick={handleStartJudging}
            className="start-judging-btn"
          >
            Start Judging
          </Button>
          <Button
            onClick={handleViewApplicants}
            className="view-applicants-btn"
          >
            View All Applicants
          </Button>
        </div>

        <Modal
          isOpen={showMultiTabModal}
          title="Session Ended"
          onClose={() => {
            setShowMultiTabModal(false);
            navigate("/");
          }}
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

export default AdminPage;

import React, { useState, useEffect, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import { createGetAuthToken } from "../utils/authUtils";
import "./AdminRolesPage.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminRolesPage = () => {
  const {
    getAccessTokenSilently,
    isAuthenticated,
    isLoading: authLoading,
  } = useAuth0();
  const navigate = useNavigate();
  const hasInitialized = useRef(false);

  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState(null);

  // Search state
  const [searchEmail, setSearchEmail] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState(null);

  // Users with roles state
  const [usersWithRoles, setUsersWithRoles] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // Action state
  const [actionLoading, setActionLoading] = useState(false);

  // Token helper
  const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);

  // Check admin status on mount
  useEffect(() => {
    if (hasInitialized.current) return;
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate("/", { replace: true });
      return;
    }

    hasInitialized.current = true;

    const checkAdminStatus = async () => {
      try {
        setLoading(true);
        const token = await getAuthToken();
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await axios.post(
          `${BACKEND_URL}/admin/auth/check`,
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        );

        setIsAdmin(response.data.is_admin);
        if (response.data.is_admin) {
          await loadUsersWithRoles(token);
        }
        setLoading(false);
      } catch (err) {
        console.error("Error checking admin status:", err);
        setError("Failed to verify admin status.");
        setLoading(false);
      }
    };

    checkAdminStatus();
  }, [authLoading, isAuthenticated, navigate, getAccessTokenSilently]);

  const loadUsersWithRoles = async (token) => {
    try {
      setUsersLoading(true);
      const response = await axios.get(`${BACKEND_URL}/roles/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsersWithRoles(response.data.users);
      setUsersLoading(false);
    } catch (err) {
      console.error("Error loading users:", err);
      setUsersLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchEmail.trim()) return;

    try {
      setSearchLoading(true);
      setSearchError(null);
      setSearchResults([]);

      const token = await getAuthToken();
      if (!token) return;

      const response = await axios.get(
        `${BACKEND_URL}/roles/search-user?email=${encodeURIComponent(searchEmail.trim())}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      setSearchResults(response.data.auth0_users);
      if (response.data.auth0_users.length === 0) {
        setSearchError("No users found with that email in Auth0.");
      }
      setSearchLoading(false);
    } catch (err) {
      console.error("Error searching users:", err);
      setSearchError(err.response?.data?.detail || "Failed to search users.");
      setSearchLoading(false);
    }
  };

  const handleGrantRole = async (auth0Id, email, name, role) => {
    try {
      setActionLoading(true);
      const token = await getAuthToken();
      if (!token) return;

      await axios.post(
        `${BACKEND_URL}/roles/grant`,
        { auth0_id: auth0Id, email: email, role: role, name: name },
        { headers: { Authorization: `Bearer ${token}` } },
      );

      // Refresh the users list
      await loadUsersWithRoles(token);
      setActionLoading(false);
    } catch (err) {
      console.error("Error granting role:", err);
      setError(err.response?.data?.detail || "Failed to grant role.");
      setActionLoading(false);
    }
  };

  const handleRevokeRole = async (userId, role) => {
    try {
      setActionLoading(true);
      const token = await getAuthToken();
      if (!token) return;

      await axios.post(
        `${BACKEND_URL}/roles/revoke`,
        { user_id: userId, role: role },
        { headers: { Authorization: `Bearer ${token}` } },
      );

      // Refresh the users list
      await loadUsersWithRoles(token);
      setActionLoading(false);
    } catch (err) {
      console.error("Error revoking role:", err);
      setError(err.response?.data?.detail || "Failed to revoke role.");
      setActionLoading(false);
    }
  };

  if (authLoading || loading) {
    return <FullPageLoadingSpinner />;
  }

  if (!isAdmin) {
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="roles-container">
          <div className="roles-header">
            <h1 className="roles-title">Not Authorized</h1>
            <p className="roles-subtitle">
              You do not have permission to access this page.
            </p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <WhiteBackground />
      <div className="roles-container">
        <div className="roles-header">
          <h1 className="roles-title">Role Management</h1>
          <p className="roles-subtitle">Manage user roles and permissions</p>
        </div>

        {error && <div className="roles-error">{error}</div>}

        {/* Search Section */}
        <div className="roles-section">
          <h2 className="section-title">Add User Role</h2>
          <p className="section-description">
            Search for a user by their Auth0 email to grant them a role.
          </p>
          <div className="search-form">
            <input
              type="email"
              className="search-input"
              placeholder="Enter email address..."
              value={searchEmail}
              onChange={(e) => setSearchEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button
              onClick={handleSearch}
              disabled={searchLoading || !searchEmail.trim()}
            >
              {searchLoading ? "Searching..." : "Search"}
            </Button>
          </div>

          {searchError && <div className="search-error">{searchError}</div>}

          {searchResults.length > 0 && (
            <div className="search-results">
              <h3>Search Results</h3>
              {searchResults.map((user) => (
                <div key={user.auth0_id} className="search-result-item">
                  <div className="user-info">
                    {user.picture && (
                      <img src={user.picture} alt="" className="user-avatar" />
                    )}
                    <div className="user-details">
                      <span className="user-name">
                        {user.name || user.email}
                      </span>
                      <span className="user-email">{user.email}</span>
                    </div>
                  </div>
                  <div className="role-actions">
                    <Button
                      onClick={() =>
                        handleGrantRole(
                          user.auth0_id,
                          user.email,
                          user.name,
                          "admin",
                        )
                      }
                      disabled={actionLoading}
                      className="grant-btn admin-grant"
                    >
                      Grant Admin
                    </Button>
                    <Button
                      onClick={() =>
                        handleGrantRole(
                          user.auth0_id,
                          user.email,
                          user.name,
                          "check_in",
                        )
                      }
                      disabled={actionLoading}
                      className="grant-btn checkin-grant"
                    >
                      Grant Check-In
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Current Users Section */}
        <div className="roles-section">
          <h2 className="section-title">Users with Roles</h2>
          <p className="section-description">
            All users who have been granted at least one role.
          </p>

          {usersLoading ? (
            <div className="loading-text">Loading users...</div>
          ) : usersWithRoles.length === 0 ? (
            <div className="no-users">
              No users have been granted roles yet.
            </div>
          ) : (
            <div className="users-list">
              {usersWithRoles.map((user) => (
                <div key={user.user_id} className="user-card">
                  <div className="user-card-info">
                    <span className="user-card-name">
                      {user.first_name || user.last_name
                        ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
                        : "Unknown User"}
                    </span>
                    <span className="user-card-email">
                      {user.email || user.auth0_id}
                    </span>
                  </div>
                  <div className="user-card-roles">
                    {user.roles.map((role) => (
                      <div key={role} className={`role-badge ${role}`}>
                        <span className="role-name">{role}</span>
                        <button
                          className="role-remove-btn"
                          onClick={() => handleRevokeRole(user.user_id, role)}
                          disabled={actionLoading}
                          title={`Remove ${role} role`}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Back Button */}
        <div className="roles-actions">
          <Button onClick={() => navigate("/admin")} className="back-btn">
            Back to Admin
          </Button>
        </div>
      </div>
    </>
  );
};

export default AdminRolesPage;

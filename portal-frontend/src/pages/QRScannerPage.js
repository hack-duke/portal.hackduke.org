import React, { useState, useEffect, useRef, useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import jsQR from "jsqr";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import { createGetAuthToken } from "../utils/authUtils";
import "./QRScannerPage.css";

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/check_in`;

// Convert UTC military time to 12-hour Eastern Time format
const formatTime = (militaryTime) => {
  if (!militaryTime) return "";

  // Create a date object for today with the given UTC time
  const [hours, minutes] = militaryTime.split(":").map(Number);
  const now = new Date();
  const utcDate = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate(),
      hours,
      minutes,
    ),
  );

  // Format to Eastern Time
  return utcDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "America/New_York",
  });
};

const QRScannerPage = () => {
  const {
    getAccessTokenSilently,
    isAuthenticated,
    isLoading: authLoading,
  } = useAuth0();
  const navigate = useNavigate();

  // Access check state (check_in role required)
  const [accessLoading, setAccessLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);
  const [accessError, setAccessError] = useState(null);
  const hasCheckedAccess = useRef(false);
  const authTokenRef = useRef(null);

  const [eventType, setEventType] = useState("check-in");
  const [scannerActive, setScannerActive] = useState(false);
  const [status, setStatus] = useState({
    message: "Tap 'Open Scanner' to begin",
    type: "waiting",
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [checkedInLog, setCheckedInLog] = useState([]);
  const [checkedInCount, setCheckedInCount] = useState(0);
  const [logSearchQuery, setLogSearchQuery] = useState("");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanningRef = useRef(true);
  const searchTimeoutRef = useRef(null);

  // Check access on mount (check_in role required)
  useEffect(() => {
    if (hasCheckedAccess.current) return;
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate("/", { replace: true });
      return;
    }

    hasCheckedAccess.current = true;

    const checkAccessStatus = async () => {
      try {
        const getAuthToken = createGetAuthToken(
          getAccessTokenSilently,
          setAccessError,
        );
        const token = await getAuthToken();
        if (!token) {
          setAccessLoading(false);
          return;
        }

        // Store token for API calls
        authTokenRef.current = token;

        const response = await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/admin/auth/check`,
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        );

        // User has access if they have check_in role
        const roles = response.data.roles || [];
        const canAccess = roles.includes("check_in");
        setHasAccess(canAccess);
        setAccessLoading(false);
      } catch (err) {
        console.error("Error checking access status:", err);
        setAccessError("Failed to verify access.");
        setAccessLoading(false);
      }
    };

    checkAccessStatus();
  }, [authLoading, isAuthenticated, navigate, getAccessTokenSilently]);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);

  const loadLog = useCallback(() => {
    if (!authTokenRef.current) return;

    fetch(`${API_BASE}/log?event_type=${encodeURIComponent(eventType)}`, {
      headers: {
        Authorization: `Bearer ${authTokenRef.current}`,
      },
    })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load log");
        return response.json();
      })
      .then((data) => {
        setCheckedInCount(data.total_users);
        setCheckedInLog(data.log);
      })
      .catch((err) => {
        console.error("Error loading log:", err);
      });
  }, [eventType]);

  const sendQRCode = useCallback(
    (data) => {
      if (!authTokenRef.current) return;

      fetch(`${API_BASE}/log_user`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authTokenRef.current}`,
        },
        body: JSON.stringify({ qr_code: data, event_type: eventType }),
      })
        .then((response) => {
          if (!response.ok) {
            return response.json().then((errData) => {
              throw new Error(errData.detail || "Network response was not ok");
            });
          }
          return response.json();
        })
        .then((data) => {
          setStatus({
            message: (
              <>
                <strong>{data.full_name}</strong> checked in!
                <br />
                <small>
                  Event: {data.event_type} | Time:{" "}
                  {formatTime(data.check_in_time)} | Status: {data.status}
                </small>
              </>
            ),
            type: "success",
          });
          loadLog();
        })
        .catch((err) => {
          console.error("Error sending QR code data:", err);
          setStatus({ message: "Error: " + err.message, type: "error" });
        });
    },
    [eventType, loadLog],
  );

  const scanFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      const ctx = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);

      if (code && scanningRef.current) {
        scanningRef.current = false;
        sendQRCode(code.data);

        setTimeout(() => {
          scanningRef.current = true;
          setStatus({ message: "Ready to scan next code", type: "waiting" });
        }, 2000);
      }
    }
    animationFrameRef.current = requestAnimationFrame(scanFrame);
  }, [sendQRCode]);

  const initCamera = useCallback(async () => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const constraints = {
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        videoRef.current.onloadedmetadata = () => {
          if (videoRef.current) {
            videoRef.current
              .play()
              .then(() => {
                setScannerActive(true);
                animationFrameRef.current = requestAnimationFrame(scanFrame);
                setStatus({
                  message: "Camera active. Point at a QR code.",
                  type: "waiting",
                });
              })
              .catch((err) => {
                if (err.name !== "AbortError") {
                  console.error("Error playing video:", err);
                }
              });
          }
        };
      }
    } catch (err) {
      console.error("Error accessing the camera:", err);
      setStatus({
        message: "Camera access denied: " + err.message,
        type: "error",
      });
    }
  }, [scanFrame]);

  const stopCamera = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.onloadedmetadata = null;
      videoRef.current.srcObject = null;
    }
    setScannerActive(false);
  }, []);

  const toggleScanner = () => {
    if (scannerActive) {
      stopCamera();
      setStatus({
        message: "Scanner closed. Use manual search below.",
        type: "waiting",
      });
    } else {
      initCamera();
    }
  };

  const searchUsers = (query) => {
    if (!authTokenRef.current) return;

    fetch(`${API_BASE}/search_users?q=${encodeURIComponent(query)}`, {
      headers: {
        Authorization: `Bearer ${authTokenRef.current}`,
      },
    })
      .then((response) => {
        if (!response.ok) throw new Error("Search failed");
        return response.json();
      })
      .then((data) => {
        setSearchResults(data.users || []);
      })
      .catch((err) => {
        console.error("Search error:", err);
        setSearchResults([]);
      });
  };

  const handleSearchInput = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(() => {
      searchUsers(query.trim());
    }, 300);
  };

  const checkInUser = (userId) => {
    if (!authTokenRef.current) return;

    fetch(`${API_BASE}/log_user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authTokenRef.current}`,
      },
      body: JSON.stringify({ qr_code: userId, event_type: eventType }),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((errData) => {
            throw new Error(errData.detail || "Check-in failed");
          });
        }
        return response.json();
      })
      .then((data) => {
        setStatus({
          message: (
            <>
              <strong>{data.full_name}</strong> checked in!
              <br />
              <small>
                Event: {data.event_type} | Time:{" "}
                {formatTime(data.check_in_time)} | Status: {data.status}
              </small>
            </>
          ),
          type: "success",
        });
        setSearchQuery("");
        setSearchResults([]);
        loadLog();

        setTimeout(() => {
          setStatus({ message: "Ready to scan next code", type: "waiting" });
        }, 2000);
      })
      .catch((err) => {
        setStatus({ message: "Error: " + err.message, type: "error" });
      });
  };

  // Filter log based on search query
  const filteredLog = checkedInLog.filter((entry) =>
    entry.name.toLowerCase().includes(logSearchQuery.toLowerCase()),
  );

  // Load data once we have access (camera starts closed by default)
  useEffect(() => {
    if (hasAccess && authTokenRef.current) {
      loadLog();
    }

    return () => {
      stopCamera();
    };
  }, [hasAccess, loadLog, stopCamera]);

  // Reload data when event type changes
  useEffect(() => {
    if (hasAccess && authTokenRef.current) {
      loadLog();
    }
  }, [eventType, hasAccess, loadLog]);

  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopCamera();
      } else if (scannerActive) {
        initCamera();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [scannerActive, initCamera, stopCamera]);

  // Show loading while checking access
  if (authLoading || accessLoading) {
    return <FullPageLoadingSpinner />;
  }

  // Show error if access check failed
  if (accessError) {
    return (
      <>
        <WhiteBackground />
        <div className="qr-scanner-page">
          <div className="qr-container">
            <div className="qr-header">
              <h1 className="qr-title">Error</h1>
              <p className="qr-subtitle">{accessError}</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Show not authorized if user doesn't have check_in role
  if (!hasAccess) {
    return (
      <>
        <WhiteBackground />
        <div className="qr-scanner-page">
          <div className="qr-container">
            <div className="qr-header">
              <h1 className="qr-title">Not Authorized</h1>
              <p className="qr-subtitle">
                You need the check-in role to access this page.
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* <Navbar /> */}
      <WhiteBackground />
      <div className="qr-scanner-page">
        <div className="qr-container">
          <div className="qr-header">
            <h1 className="qr-title">QR Scanner</h1>
            <p className="qr-subtitle">Scan attendee QR codes for check-in</p>
          </div>

          <select
            className="event-select"
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            <option value="check-in">Check-In</option>
            <option value="lunch">Sat Lunch</option>
            <option value="dinner">Sat Dinner</option>
            <option value="brekky">Sun Brekky</option>
          </select>

          {/* Scanner Section - transforms to fullscreen overlay on mobile when active */}
          <div
            className={`scanner-section ${scannerActive ? "scanner-active" : ""}`}
          >
            <button
              className={`scanner-toggle-btn ${scannerActive ? "active" : "inactive"}`}
              onClick={toggleScanner}
            >
              {scannerActive ? "Close Scanner" : "Open Scanner"}
            </button>
            <div
              className={`scanner-container ${!scannerActive ? "hidden" : ""}`}
            >
              <video ref={videoRef} autoPlay playsInline muted></video>
              <canvas ref={canvasRef}></canvas>
            </div>
            <div className={`status-card ${status.type}`}>
              {typeof status.message === "string"
                ? status.message
                : status.message}
            </div>
          </div>

          {/* Manual Search Section */}
          <div className="card manual-search-section">
            <h2>Manual Search</h2>
            <input
              type="text"
              className="search-input"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={handleSearchInput}
            />
            <div className="search-hint">
              Type at least 2 characters to search
            </div>
            <div className="search-results">
              {searchResults.length === 0 && searchQuery.length >= 2 && (
                <div className="no-results">No users found</div>
              )}
              {searchResults.map((user) => (
                <div key={user.user_id} className="user-result">
                  <span className="user-name">{user.name}</span>
                  <button
                    className="check-in-btn"
                    onClick={() => checkInUser(user.user_id)}
                  >
                    Check In
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Check-in Log Section */}
          <div className="card log-section">
            <div className="log-header">
              <h2>Check-in Log</h2>
              <button className="refresh-btn" onClick={loadLog}>
                Refresh
              </button>
            </div>
            <div className="stat-badge">
              <span className="stat-number">{checkedInCount}</span>
              <span className="stat-label">Checked In</span>
            </div>
            <input
              type="text"
              className="log-search-input"
              placeholder="Search log..."
              value={logSearchQuery}
              onChange={(e) => setLogSearchQuery(e.target.value)}
            />
            <div className="log-list">
              {filteredLog.length === 0 ? (
                <div className="no-results">
                  {checkedInLog.length === 0
                    ? "No check-ins yet"
                    : "No matches found"}
                </div>
              ) : (
                filteredLog.map((entry, index) => (
                  <div key={index} className="log-item">
                    <span className="log-name">{entry.name}</span>
                    <span className="log-time">{formatTime(entry.time)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default QRScannerPage;

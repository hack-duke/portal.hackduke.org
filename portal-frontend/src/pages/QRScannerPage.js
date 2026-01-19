import React, { useState, useEffect, useRef, useCallback } from "react";
import jsQR from "jsqr";
import "./QRScannerPage.css";

const API_BASE = "/check-in";

const QRScannerPage = () => {
  const [eventType, setEventType] = useState("check-in");
  const [scannerActive, setScannerActive] = useState(true);
  const [status, setStatus] = useState({ message: "Waiting for camera...", type: "waiting" });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [checkedInLog, setCheckedInLog] = useState([]);
  const [checkedInCount, setCheckedInCount] = useState(0);
  const [notCheckedInList, setNotCheckedInList] = useState([]);
  const [notCheckedInCount, setNotCheckedInCount] = useState(0);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanningRef = useRef(true);
  const searchTimeoutRef = useRef(null);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);

  const loadLog = useCallback(() => {
    fetch(`${API_BASE}/log?event_type=${encodeURIComponent(eventType)}`)
      .then((response) => response.json())
      .then((data) => {
        setCheckedInCount(data.total_users);
        setCheckedInLog(data.log);
      })
      .catch((err) => {
        console.error("Error loading log:", err);
      });
  }, [eventType]);

  const loadNotCheckedIn = useCallback(() => {
    fetch(`${API_BASE}/not_checked_in?event_type=${encodeURIComponent(eventType)}`)
      .then((response) => response.json())
      .then((data) => {
        setNotCheckedInCount(data.total);
        setNotCheckedInList(data.users);
      })
      .catch((err) => {
        console.error("Error loading not checked in:", err);
      });
  }, [eventType]);

  const sendQRCode = useCallback(
    (data) => {
      fetch(`${API_BASE}/log_user`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
                  Event: {data.event_type} | Time: {data.check_in_time} | Status: {data.status}
                </small>
              </>
            ),
            type: "success",
          });
          loadLog();
          loadNotCheckedIn();
        })
        .catch((err) => {
          console.error("Error sending QR code data:", err);
          setStatus({ message: "Error: " + err.message, type: "error" });
        });
    },
    [eventType, loadLog, loadNotCheckedIn]
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
        setStatus({ message: "User found: " + code.data, type: "success" });

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
      // Stop any existing stream first
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

        // Wait for video to be ready before playing
        videoRef.current.onloadedmetadata = () => {
          if (videoRef.current) {
            videoRef.current.play().then(() => {
              setScannerActive(true);
              animationFrameRef.current = requestAnimationFrame(scanFrame);
              setStatus({ message: "Camera active. Point at a QR code.", type: "waiting" });
            }).catch((err) => {
              // Ignore AbortError which happens when play is interrupted
              if (err.name !== "AbortError") {
                console.error("Error playing video:", err);
              }
            });
          }
        };
      }
    } catch (err) {
      console.error("Error accessing the camera:", err);
      setStatus({ message: "Camera access denied: " + err.message, type: "error" });
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
      setStatus({ message: "Scanner closed. Use manual search below.", type: "waiting" });
    } else {
      initCamera();
    }
  };

  const searchUsers = (query) => {
    fetch(`${API_BASE}/search_users?q=${encodeURIComponent(query)}`)
      .then((response) => response.json())
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

  const checkInUser = (userId, userName) => {
    fetch(`${API_BASE}/log_user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
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
                Event: {data.event_type} | Time: {data.check_in_time} | Status: {data.status}
              </small>
            </>
          ),
          type: "success",
        });
        setSearchQuery("");
        setSearchResults([]);
        loadLog();
        loadNotCheckedIn();

        setTimeout(() => {
          setStatus({ message: "Ready to scan next code", type: "waiting" });
        }, 3000);
      })
      .catch((err) => {
        setStatus({ message: "Error: " + err.message, type: "error" });
      });
  };

  // Initialize camera and load data on mount
  useEffect(() => {
    initCamera();
    loadLog();
    loadNotCheckedIn();

    return () => {
      stopCamera();
    };
  }, [initCamera, loadLog, loadNotCheckedIn, stopCamera]);

  // Reload data when event type changes
  useEffect(() => {
    loadLog();
    loadNotCheckedIn();
  }, [eventType, loadLog, loadNotCheckedIn]);

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

  return (
    <div className="qr-scanner-page">
      <div className="qr-container">
        <h1>QR Code Scanner</h1>

        <select
          id="event-select"
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
        >
          <option value="check-in">Check-In</option>
          <option value="lunch">Sat Lunch</option>
          <option value="dinner">Sat Dinner</option>
          <option value="brekky">Sun Brekky</option>
        </select>

        <div className="scanner-section">
          <button
            className={`scanner-toggle-btn ${scannerActive ? "active" : "inactive"}`}
            onClick={toggleScanner}
          >
            {scannerActive ? "Close Scanner" : "Open Scanner"}
          </button>
          <div className={`scanner-container ${!scannerActive ? "hidden" : ""}`}>
            <video ref={videoRef} autoPlay playsInline muted></video>
            <canvas ref={canvasRef}></canvas>
          </div>
        </div>

        <div className={`status ${status.type}`}>
          {typeof status.message === "string" ? status.message : status.message}
        </div>

        {/* Manual Search Section */}
        <div className="manual-search-section">
          <h2>Manual Search</h2>
          <input
            type="text"
            id="user-search"
            placeholder="Search by name..."
            value={searchQuery}
            onChange={handleSearchInput}
          />
          <div className="search-hint">Type at least 2 characters to search</div>
          <div className="search-results">
            {searchResults.length === 0 && searchQuery.length >= 2 && (
              <div className="no-results">No users found</div>
            )}
            {searchResults.map((user) => (
              <div key={user.user_id} className="user-result">
                <span className="user-name">{user.name}</span>
                <button
                  className="check-in-btn"
                  onClick={() => checkInUser(user.user_id, user.name)}
                >
                  Check In
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Check-in Log Section */}
        <div className="attendees-section">
          <h2>Check-in Log</h2>
          <button className="refresh-btn" onClick={loadLog}>
            Refresh
          </button>
          <div className="attendees-stats">
            <div className="stat">
              <div className="stat-number">{checkedInCount}</div>
              <div className="stat-label">Checked In</div>
            </div>
          </div>
          <div className="attendees-list">
            {checkedInLog.length === 0 ? (
              <div className="no-results">No check-ins yet</div>
            ) : (
              checkedInLog.map((entry, index) => (
                <div key={index} className="attendee-item">
                  <div className="attendee-info">
                    <span className="attendee-name">{entry.name}</span>
                    <span className="checked-in-badge">{entry.time}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Not Checked In Section */}
        <div className="attendees-section">
          <h2>Not Checked In</h2>
          <button className="refresh-btn" onClick={loadNotCheckedIn}>
            Refresh
          </button>
          <div className="attendees-stats">
            <div className="stat">
              <div className="stat-number">{notCheckedInCount}</div>
              <div className="stat-label">Remaining</div>
            </div>
          </div>
          <div className="attendees-list">
            {notCheckedInList.length === 0 ? (
              <div className="no-results">Everyone has checked in!</div>
            ) : (
              notCheckedInList.map((user, index) => (
                <div key={index} className="attendee-item">
                  <div className="attendee-info">
                    <span className="attendee-name">{user.name}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRScannerPage;

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { Link } from "react-router-dom";
import axios from "axios";
import jsQR from "jsqr";
import { createGetAuthToken } from "../utils/authUtils";
import "./DuQuantumPortal.css";
import "./DuQuantumAdminPage.css";

const EVENT_SLUG = "duquantum-2026";
const CHECKPOINTS = [
  { value: "arrival", label: "Arrival" },
  { value: "saturday_lunch", label: "Saturday lunch" },
  { value: "saturday_dinner", label: "Saturday dinner" },
  { value: "sunday_brunch", label: "Sunday brunch" },
];

const errorMessage = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return "The pass could not be checked in.";
};

const displayName = (record) =>
  record.preferred_name ||
  [record.first_name, record.last_name].filter(Boolean).join(" ") ||
  "Attendee";

const DuQuantumScannerPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [checkpoint, setCheckpoint] = useState("arrival");
  const [manualPass, setManualPass] = useState("");
  const [scannerActive, setScannerActive] = useState(false);
  const [cameraStarting, setCameraStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loadingLog, setLoadingLog] = useState(true);
  const [recentCheckIns, setRecentCheckIns] = useState([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState({
    type: "idle",
    message: "Ready to scan an event pass.",
  });
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const frameRef = useRef(null);
  const scanReadyRef = useRef(true);
  const pendingRef = useRef(false);
  const submitPassRef = useRef(null);
  const lastCodeRef = useRef(null);
  const cameraSessionRef = useRef(0);
  const startingRef = useRef(false);
  const logRequestRef = useRef(0);

  const getToken = useCallback(async () => {
    const authToken = createGetAuthToken(getAccessTokenSilently, (message) =>
      setStatus({ type: "error", message }),
    );
    return authToken();
  }, [getAccessTokenSilently]);

  const loadLog = useCallback(async () => {
    const request = ++logRequestRef.current;
    setLoadingLog(true);
    try {
      const token = await getToken();
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/check-ins`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { checkpoint, limit: 100 },
        },
      );
      if (request === logRequestRef.current) {
        setRecentCheckIns(response.data?.check_ins || []);
        setTotal(response.data?.total || 0);
      }
    } catch (error) {
      if (request !== logRequestRef.current) return;
      setStatus({
        type: "error",
        message:
          error?.response?.status === 403
            ? "This account needs the check-in role to use the DuQuantum scanner."
            : errorMessage(error),
      });
    } finally {
      if (request === logRequestRef.current) setLoadingLog(false);
    }
  }, [checkpoint, getToken]);

  useEffect(() => {
    loadLog();
  }, [loadLog]);

  const submitPass = useCallback(
    async (passId) => {
      const value = String(passId || "").trim();
      if (!value || pendingRef.current) return;
      pendingRef.current = true;
      setSubmitting(true);
      scanReadyRef.current = false;
      setStatus({ type: "working", message: "Verifying DuQuantum pass…" });
      try {
        const token = await getToken();
        const response = await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/check-ins`,
          { pass_id: value, checkpoint },
          { headers: { Authorization: `Bearer ${token}` } },
        );
        const record = response.data;
        setStatus({
          type: "success",
          message: `${displayName(record)} checked in for ${CHECKPOINTS.find((item) => item.value === checkpoint)?.label || checkpoint}.`,
        });
        setManualPass("");
        await loadLog();
      } catch (error) {
        setStatus({
          type: error?.response?.status === 409 ? "warning" : "error",
          message: errorMessage(error),
        });
        if (error?.response?.status === 409) await loadLog();
      } finally {
        pendingRef.current = false;
        setSubmitting(false);
        scanReadyRef.current = true;
      }
    },
    [checkpoint, getToken, loadLog],
  );

  useEffect(() => {
    submitPassRef.current = submitPass;
  }, [submitPass]);

  const scanFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (
      video &&
      canvas &&
      video.readyState >= 2 &&
      video.videoWidth > 0 &&
      video.videoHeight > 0
    ) {
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (context) {
        canvas.width = Math.min(video.videoWidth, 1280);
        canvas.height = Math.round(
          (video.videoHeight * canvas.width) / video.videoWidth,
        );
        try {
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const image = context.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(image.data, image.width, image.height);
          if (!code?.data) lastCodeRef.current = null;
          else if (scanReadyRef.current && code.data !== lastCodeRef.current) {
            lastCodeRef.current = code.data;
            submitPassRef.current?.(code.data);
          }
        } catch (_) {
          // A transient video frame can be unavailable while the camera warms up.
        }
      }
    }
    frameRef.current = window.requestAnimationFrame(scanFrame);
  }, []);

  const stopCamera = useCallback(() => {
    cameraSessionRef.current += 1;
    startingRef.current = false;
    if (frameRef.current !== null)
      window.cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    if (streamRef.current)
      streamRef.current.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setScannerActive(false);
    setCameraStarting(false);
    lastCodeRef.current = null;
  }, []);

  const startCamera = async () => {
    if (startingRef.current || streamRef.current) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus({
        type: "error",
        message:
          "Camera access requires a supported browser over HTTPS. Use the manual pass field or check in by name in the attendee manifest.",
      });
      return;
    }
    startingRef.current = true;
    setCameraStarting(true);
    const session = ++cameraSessionRef.current;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      if (session !== cameraSessionRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      if (session !== cameraSessionRef.current) return;
      setScannerActive(true);
      setStatus({
        type: "idle",
        message: "Camera active. Center a DuQuantum pass in the frame.",
      });
      frameRef.current = window.requestAnimationFrame(scanFrame);
    } catch (error) {
      if (session !== cameraSessionRef.current) return;
      stopCamera();
      setStatus({
        type: "error",
        message:
          error.name === "NotAllowedError"
            ? "Camera permission was denied. Allow camera access in your browser settings, or check in by name in the attendee manifest."
            : `Camera unavailable: ${error.message}. You can use a manual pass ID or check in by name in the attendee manifest.`,
      });
    } finally {
      if (session === cameraSessionRef.current) {
        startingRef.current = false;
        setCameraStarting(false);
      }
    }
  };

  useEffect(() => stopCamera, [stopCamera]);

  return (
    <main className="dq-admin-page dq-scanner-page">
      <div className="dq-circuit" aria-hidden="true" />
      <header className="dq-header">
        <Link
          className="dq-brand"
          to="/events/duquantum-2026"
          aria-label="DuQuantum attendee portal"
        >
          <img src="/duquantum-2026/logo.svg" alt="DuQuantum" />
          <span>STAFF // CHECK-IN</span>
        </Link>
        <nav className="dq-header-actions" aria-label="Scanner navigation">
          <Link to="/admin/events/duquantum-2026/attendees">
            Attendee manifest
          </Link>
          <Link to="/admin">HackDuke admin</Link>
        </nav>
      </header>

      <section className="dq-scanner-shell" aria-labelledby="scanner-title">
        <div className="dq-admin-title-row">
          <div>
            <p className="dq-eyebrow">DUQUANTUM 2026 // EVENT-SCOPED PASSES</p>
            <h1 id="scanner-title">Check-in scanner</h1>
            <p>
              Only DuQuantum pass IDs are accepted here. Legacy HackDuke user QR
              codes will not check in.
            </p>
          </div>
          <label className="dq-checkpoint-select">
            <span>Checkpoint</span>
            <select
              value={checkpoint}
              disabled={submitting}
              onChange={(event) => {
                lastCodeRef.current = null;
                setCheckpoint(event.target.value);
              }}
            >
              {CHECKPOINTS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="dq-scanner-grid">
          <section className="dq-camera-panel" aria-labelledby="camera-heading">
            <div className="dq-camera-heading">
              <div>
                <p className="dq-terminal-label">
                  OPTICAL_READER // {scannerActive ? "ACTIVE" : "STANDBY"}
                </p>
                <h2 id="camera-heading">Scan QR pass</h2>
              </div>
              <button
                className={
                  scannerActive ? "dq-stop-button" : "dq-primary-button"
                }
                type="button"
                onClick={scannerActive ? stopCamera : startCamera}
                disabled={cameraStarting}
              >
                {cameraStarting
                  ? "Opening camera…"
                  : scannerActive
                    ? "Close camera"
                    : "Open camera"}
              </button>
            </div>
            <div
              className={`dq-camera-frame ${scannerActive ? "is-active" : ""}`}
            >
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                aria-label="Camera preview"
              />
              <canvas ref={canvasRef} aria-hidden="true" />
              {!scannerActive && <p>Camera is off</p>}
              <span aria-hidden="true" />
            </div>
            <div
              className={`dq-scan-status ${status.type}`}
              role="status"
              aria-live="assertive"
            >
              {status.message}
            </div>
            <form
              className="dq-manual-pass"
              onSubmit={(event) => {
                event.preventDefault();
                submitPass(manualPass);
              }}
            >
              <label htmlFor="manual-pass-id">Manual pass ID</label>
              <div>
                <input
                  id="manual-pass-id"
                  value={manualPass}
                  onChange={(event) => setManualPass(event.target.value)}
                  autoComplete="off"
                  placeholder="Paste the opaque pass ID"
                />
                <button
                  className="dq-secondary-button"
                  type="submit"
                  disabled={submitting || manualPass.trim().length < 10}
                >
                  Check in
                </button>
              </div>
            </form>
          </section>

          <aside className="dq-checkin-log" aria-labelledby="checkin-log-title">
            <div className="dq-log-heading">
              <div>
                <p className="dq-terminal-label">
                  CHECKPOINT_LOG // {checkpoint.toUpperCase()}
                </p>
                <h2 id="checkin-log-title">Recent check-ins</h2>
              </div>
              <strong>{total}</strong>
            </div>
            {loadingLog ? (
              <p className="dq-log-empty">Loading log…</p>
            ) : recentCheckIns.length ? (
              <ol>
                {recentCheckIns.map((record) => (
                  <li key={record.id}>
                    <div>
                      <strong>{displayName(record)}</strong>
                      <span>{record.checkpoint.replace(/_/g, " ")}</span>
                    </div>
                    <time dateTime={record.checked_in_at}>
                      {new Date(record.checked_in_at).toLocaleTimeString(
                        "en-US",
                        {
                          hour: "numeric",
                          minute: "2-digit",
                          timeZone: "America/New_York",
                        },
                      )}
                    </time>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="dq-log-empty">
                No check-ins at this checkpoint yet.
              </p>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
};

export default DuQuantumScannerPage;

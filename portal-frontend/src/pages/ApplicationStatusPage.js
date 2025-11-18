import React, { useEffect, useState } from "react";
import HeroBackground from "../components/HeroBackground";
import { Navbar } from "../components/Navbar";
import "./ApplicationStatusPage.css";
import { useAuth0 } from "@auth0/auth0-react";
import { formatDistanceToNow } from "date-fns";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import { useWindowSize } from "react-use";
import Confetti from "react-confetti";
import { useLocation } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import Button from "../components/Button";
import axios from "axios";
import { useNavigate } from "react-router-dom";

// defaulting this, but only shd happen if page is navigated to directly (no query args)
const DEFAULT_FORM_KEY = "2025-cfg-application";

const StatusList = ({ statusItems }) => {
  return (
    <div className="status-grid">
      {statusItems.map((item, index) => (
        <div key={index}>
          <div className="status-label">{item.label}</div>
          <div className="status-value">{item.value}</div>
        </div>
      ))}
    </div>
  );
};

const formatApplication = (application) => {
  const form_data = application["form_data"];
  const ret = [];

  ret.push({ label: "Status", value: application["status"] });

  ret.push({
    label: "Submitted",
    value: formatDistanceToNow(new Date(application["created_at"] + "Z"), {
      addSuffix: true,
    }),
  });

  if (form_data) {
    Object.entries(form_data).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") {
        return;
      }

      if (typeof value === "string" && value.length > 100) {
        return;
      }

      const label = key
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");

      let displayValue = value;
      if (typeof value === "boolean") {
        displayValue = value ? "Yes" : "No";
      }

      ret.push({ label, value: displayValue });
    });
  }

  return ret;
};

const ApplicationStatusPage = () => {
  const { user, getAccessTokenSilently } = useAuth0();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const { width, height } = useWindowSize();
  const location = useLocation();
  const navigate = useNavigate();
  const { firstTime } = location.state || {};

  const searchParams = new URLSearchParams(location.search);
  const formKey = searchParams.get("formKey") || DEFAULT_FORM_KEY;

  useEffect(() => {
    const checkIfSubmitted = async () => {
      try {
        setLoading(true);
        const token = await getAccessTokenSilently();
        const response = await axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/application`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            params: {
              form_key: formKey,
            },
          }
        );
        setApplication(response.data);
      } catch (error) {
        if (error.response?.status === 404) {
          navigate("/application");
        } else {
          setError(error.response?.data?.error);
        }
      } finally {
        setLoading(false);
      }
    };

    checkIfSubmitted();
  }, [getAccessTokenSilently, navigate, formKey]);

  return (
    <>
      <Navbar />
      <HeroBackground />
      {loading && <FullPageLoadingSpinner />}
      {firstTime && (
        <div className="confetti">
          <Confetti
            width={width}
            height={height}
            recycle={false}
            numberOfPieces={400}
          />
        </div>
      )}
      <h1 className="status-title">Form Status</h1>
      {error && <p>{error}</p>}

      {application && (
        <div className="status-container">
          <StatusList statusItems={formatApplication(application)} />
        </div>
      )}

      {application && application["status"] === "confirmed" && (
        <>
          <Button
            variant="secondary"
            className="checkin-button"
            onClick={() => setShowQRModal(true)}
          >
            Check-In Code
          </Button>
          {showQRModal && (
            <div
              className="qr-modal-overlay"
              onClick={() => setShowQRModal(false)}
            >
              {/* TODO: Componentize this */}
              <div className="qr-modal-content">
                <QRCodeSVG
                  value={user.sub}
                  size={Math.min(width * 0.8, height * 0.8)}
                  marginSize={2}
                  minVersion={6}
                />
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
};

export default ApplicationStatusPage;

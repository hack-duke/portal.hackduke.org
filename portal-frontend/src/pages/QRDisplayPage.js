import React from "react"; // eslint-disable-line no-unused-vars
import { useSearchParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import "./QRDisplayPage.css";

const QRDisplayPage = () => {
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code") || searchParams.get("id") || "";

  if (!code) {
    return (
      <div className="qr-display-page">
        <div className="qr-display-error">
          No QR code data provided. Add <code>?code=YOUR_DATA</code> to the URL.
        </div>
      </div>
    );
  }

  return (
    <div className="qr-display-page">
      <div className="qr-display-container">
        <QRCodeSVG
          value={code}
          size={Math.min(window.innerWidth, window.innerHeight) * 0.8}
          level="H"
          marginSize={1}
        />
      </div>
    </div>
  );
};

export default QRDisplayPage;

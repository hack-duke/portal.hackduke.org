import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { createGetAuthToken } from "../utils/authUtils";

const EVENT_SLUG = "duquantum-2026";

const decodeVapidKey = (value) => {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  return Uint8Array.from(raw, (character) => character.charCodeAt(0));
};

const isIosDevice = () =>
  /iphone|ipad|ipod/i.test(window.navigator.userAgent) ||
  (window.navigator.platform === "MacIntel" &&
    window.navigator.maxTouchPoints > 1);

const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches ||
  window.navigator.standalone === true;

const DuQuantumMobileCompanion = ({ getAccessTokenSilently }) => {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [installed, setInstalled] = useState(isStandalone);
  const [config, setConfig] = useState(null);
  const [subscribed, setSubscribed] = useState(false);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState("");

  const ios = useMemo(isIosDevice, []);
  const pushSupported =
    window.isSecureContext !== false &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window;

  const authHeaders = useCallback(async () => {
    const getAuthToken = createGetAuthToken(getAccessTokenSilently, setMessage);
    const token = await getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }, [getAccessTokenSilently]);

  const loadStatus = useCallback(async () => {
    try {
      const headers = await authHeaders();
      if (!headers) return;
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/notifications`,
        { headers },
      );
      setConfig(response.data);
      if (pushSupported && Notification.permission === "granted") {
        const registration = await navigator.serviceWorker.ready;
        const browserSubscription =
          await registration.pushManager.getSubscription();
        setSubscribed(Boolean(browserSubscription && response.data.subscribed));
      } else {
        setSubscribed(false);
      }
    } catch (error) {
      setMessage(
        error?.response?.data?.detail ||
          "Event alerts are temporarily unavailable.",
      );
    }
  }, [authHeaders, pushSupported]);

  useEffect(() => {
    const handleInstallPrompt = (event) => {
      event.preventDefault();
      setInstallPrompt(event);
    };
    const handleInstalled = () => {
      setInstalled(true);
      setInstallPrompt(null);
      setMessage("DuQuantum was added to your Home Screen.");
    };
    window.addEventListener("beforeinstallprompt", handleInstallPrompt);
    window.addEventListener("appinstalled", handleInstalled);
    loadStatus();
    return () => {
      window.removeEventListener("beforeinstallprompt", handleInstallPrompt);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, [loadStatus]);

  const installApp = async () => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    if (choice?.outcome === "accepted") {
      setMessage("Finishing your DuQuantum Home Screen install…");
    }
    setInstallPrompt(null);
  };

  const enableAlerts = async () => {
    setWorking(true);
    setMessage("");
    try {
      if (!pushSupported) {
        throw new Error("This browser does not support event alerts.");
      }
      if (ios && !installed) {
        throw new Error(
          "Add the portal to your Home Screen first, open it there, then enable alerts.",
        );
      }
      if (!config?.enabled || !config?.public_key) {
        throw new Error("Event alerts are not available yet.");
      }

      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw new Error(
          "Notifications were not allowed. You can enable them in your browser or device settings.",
        );
      }

      const registration = await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: decodeVapidKey(config.public_key),
        });
      }
      const headers = await authHeaders();
      if (!headers) return;
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/notifications/subscriptions`,
        subscription.toJSON(),
        { headers },
      );
      setSubscribed(true);
      setMessage(
        `${config.schedule_count} schedule alerts are enabled for this device.`,
      );
      await registration.showNotification("DuQuantum alerts are ready", {
        body: "We’ll notify you on this device when scheduled events begin.",
        icon: "/duquantum-2026/icon-192.png",
        tag: "duquantum-2026-alerts-ready",
      });
    } catch (error) {
      setMessage(
        error?.response?.data?.detail ||
          error?.message ||
          "We could not enable event alerts.",
      );
    } finally {
      setWorking(false);
    }
  };

  const disableAlerts = async () => {
    setWorking(true);
    setMessage("");
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) await subscription.unsubscribe();
      const headers = await authHeaders();
      if (!headers) return;
      await axios.delete(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/notifications/subscriptions`,
        { headers, data: { endpoint: subscription.endpoint } },
      );
      setSubscribed(false);
      setMessage("Event alerts are off on this device.");
    } catch (error) {
      setMessage(
        error?.response?.data?.detail ||
          "We could not update your alert preference.",
      );
    } finally {
      setWorking(false);
    }
  };

  return (
    <article
      className="dq-panel dq-mobile-companion"
      aria-labelledby="dq-app-heading"
    >
      <img
        className="dq-app-icon"
        src="/duquantum-2026/icon-192.png"
        alt=""
        aria-hidden="true"
      />
      <div className="dq-app-copy">
        <p className="dq-terminal-label">MOBILE_COMPANION // OPTIONAL</p>
        <h2 id="dq-app-heading">Keep your pass one tap away</h2>
        <p>
          Add DuQuantum to your Home Screen, then opt in to live schedule alerts
          when event activities begin.
        </p>
        {ios && !installed && (
          <ol className="dq-install-steps">
            <li>Tap the Share button in Safari.</li>
            <li>Choose “Add to Home Screen,” then tap Add.</li>
            <li>Open DuQuantum from the new icon and enable alerts.</li>
          </ol>
        )}
        {!ios && !installed && !installPrompt && (
          <p className="dq-install-hint">
            Open your browser menu and choose “Add to Home screen” or “Install
            app.”
          </p>
        )}
        <div className="dq-app-actions">
          {installPrompt && !installed && (
            <button
              className="dq-secondary-button"
              type="button"
              onClick={installApp}
            >
              Add to Home Screen
            </button>
          )}
          {subscribed ? (
            <button
              className="dq-secondary-button"
              type="button"
              onClick={disableAlerts}
              disabled={working}
            >
              {working ? "Updating…" : "Turn off event alerts"}
            </button>
          ) : (
            <button
              className="dq-primary-button"
              type="button"
              onClick={enableAlerts}
              disabled={working || !config?.enabled}
            >
              {working ? "Enabling…" : "Enable event alerts"}
            </button>
          )}
        </div>
        {message && (
          <p className="dq-app-message" role="status">
            {message}
          </p>
        )}
        <p className="dq-app-privacy">
          Alerts are optional, contain schedule information only, and can be
          turned off here or in your device settings.
        </p>
      </div>
    </article>
  );
};

export default DuQuantumMobileCompanion;

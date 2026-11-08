import React, { useEffect, useMemo, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import "./DuQuantumPortal.css";
import "./DuQuantumAccountSetupPage.css";

const EVENT_SLUG = "duquantum-2026";

const readAndClearSetupToken = () => {
  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const token = new URLSearchParams(hash).get("token") || "";
  window.history.replaceState(
    {},
    document.title,
    `${window.location.pathname}${window.location.search}`,
  );
  return token;
};

const DuQuantumAccountSetupPage = () => {
  const { loginWithRedirect } = useAuth0();
  const [setupToken] = useState(readAndClearSetupToken);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [completedEmail, setCompletedEmail] = useState("");

  useEffect(() => {
    const previousTitle = document.title;
    document.title = "Set up your DuQuantum portal account";
    document.body.style.overflow = "auto";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  const requirements = useMemo(
    () => ({
      length: password.length >= 12,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      symbol: /[^A-Za-z0-9]/.test(password),
    }),
    [password],
  );
  const meetsRequirements = Object.values(requirements).every(Boolean);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (!setupToken) {
      setError(
        "This setup link is missing or incomplete. Request a new invitation from the organizers.",
      );
      return;
    }
    if (!meetsRequirements) {
      setError("Choose a password that meets every requirement below.");
      return;
    }
    if (password !== confirmation) {
      setError("The passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/events/${EVENT_SLUG}/account-setup`,
        { token: setupToken, password },
      );
      setPassword("");
      setConfirmation("");
      setCompletedEmail(response.data.login_email);
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          "We could not finish account setup. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const continueToSignIn = () =>
    loginWithRedirect({
      authorizationParams: {
        login_hint: completedEmail,
        prompt: "login",
      },
      appState: { returnTo: `/events/${EVENT_SLUG}` },
    });

  return (
    <main className="dq-page dq-setup-page">
      <div className="dq-circuit" aria-hidden="true" />
      <section className="dq-setup-shell" aria-labelledby="dq-setup-title">
        <a className="dq-setup-brand" href="https://duquantum.org/">
          <img src="/duquantum-2026/logo.svg" alt="DuQuantum 2026" />
        </a>

        <div className="dq-panel dq-setup-card">
          <p className="dq-terminal-label">
            {completedEmail ? "ACCOUNT READY" : "SECURE ACCOUNT SETUP"}
          </p>
          <h1 id="dq-setup-title">
            {completedEmail
              ? "You’re ready to sign in"
              : "Create your password"}
          </h1>

          {completedEmail ? (
            <div className="dq-setup-complete" role="status">
              <div className="dq-setup-success-mark" aria-hidden="true">
                ✓
              </div>
              <p>
                Your DuQuantum portal password is set. Sign in with{" "}
                <strong>{completedEmail}</strong> to claim and view your
                attendee pass.
              </p>
              <button
                className="dq-primary-button dq-setup-submit"
                type="button"
                onClick={continueToSignIn}
              >
                Continue to sign in
              </button>
            </div>
          ) : (
            <>
              <p className="dq-setup-intro">
                Choose a private password for your DuQuantum attendee account.
                The invitation link is single-use and your password is sent only
                over an encrypted connection.
              </p>

              {error && (
                <div className="dq-alert dq-alert-error" role="alert">
                  {error}
                </div>
              )}

              <form className="dq-setup-form" onSubmit={submit} noValidate>
                <label htmlFor="dq-password">New password</label>
                <div className="dq-password-field">
                  <input
                    id="dq-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="new-password"
                    minLength={12}
                    maxLength={128}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((visible) => !visible)}
                    aria-pressed={showPassword}
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>

                <ul
                  className="dq-password-rules"
                  aria-label="Password requirements"
                >
                  <li className={requirements.length ? "is-met" : ""}>
                    At least 12 characters
                  </li>
                  <li className={requirements.uppercase ? "is-met" : ""}>
                    One uppercase letter
                  </li>
                  <li className={requirements.lowercase ? "is-met" : ""}>
                    One lowercase letter
                  </li>
                  <li className={requirements.number ? "is-met" : ""}>
                    One number
                  </li>
                  <li className={requirements.symbol ? "is-met" : ""}>
                    One symbol
                  </li>
                </ul>

                <label htmlFor="dq-password-confirmation">
                  Confirm password
                </label>
                <input
                  id="dq-password-confirmation"
                  type={showPassword ? "text" : "password"}
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                  autoComplete="new-password"
                  minLength={12}
                  maxLength={128}
                  required
                />

                <button
                  className="dq-primary-button dq-setup-submit"
                  type="submit"
                  disabled={submitting || !setupToken}
                >
                  {submitting ? "Securing your account…" : "Create my password"}
                </button>
              </form>

              <p className="dq-setup-help">
                Link expired or already used? Contact{" "}
                <a href="mailto:organizers@duquantum.org">
                  organizers@duquantum.org
                </a>
                .
              </p>
            </>
          )}
        </div>
      </section>
    </main>
  );
};

export default DuQuantumAccountSetupPage;

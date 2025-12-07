import { useAuth0 } from "@auth0/auth0-react";

let loginWithRedirect = null;

export const setLoginWithRedirect = (loginFn) => {
  loginWithRedirect = loginFn;
};

export const createGetAuthToken = (getAccessTokenSilently, onError) => {
  return async () => {
    try {
      return await getAccessTokenSilently();
    } catch (tokenError) {
      const errorMessage = tokenError.message || "";
      const errorCode = tokenError.error || "";

      console.error("Auth token error:", {
        errorMessage,
        errorCode,
        tokenError,
      });

      if (
        errorMessage.includes("Missing Refresh Token") ||
        errorCode === "login_required" ||
        errorCode === "consent_required" ||
        errorCode === "missing_refresh_token" ||
        errorCode === "invalid_grant"
      ) {
        if (loginWithRedirect) {
          loginWithRedirect();
        } else if (onError) {
          onError("Session expired. Please log in again.");
        }
        throw tokenError;
      }

      if (errorMessage.includes("timeout") || errorCode === "timeout") {
        if (onError) {
          onError("Authentication took too long. Please try again.");
        }
        throw tokenError;
      }

      if (onError) {
        onError(
          `Authentication error: ${errorMessage || errorCode || "Unknown error"}`
        );
      }
      throw tokenError;
    }
  };
};

export const useInitializeAuth = () => {
  const { loginWithRedirect } = useAuth0();
  setLoginWithRedirect(loginWithRedirect);
};

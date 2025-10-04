import { useAuth0 } from "@auth0/auth0-react";
import { Navigate } from "react-router-dom";
import { FullPageLoadingSpinner } from "./FullPageLoadingSpinner";
import { useEffect } from "react";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      loginWithRedirect({
        appState: { returnTo: window.location.pathname },
      });
    }
  }, [isLoading, isAuthenticated, loginWithRedirect]);

  if (isLoading) {
    return <FullPageLoadingSpinner />;
  }

  return isAuthenticated ? children : null;
};

export default ProtectedRoute;

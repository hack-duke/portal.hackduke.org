import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { Auth0Provider } from "@auth0/auth0-react";
import "@fontsource/urbanist/700.css";
import "@fontsource/oxygen";

const root = ReactDOM.createRoot(document.getElementById("root"));

const getSafeReturnTo = (appState) => {
  const returnTo = appState?.returnTo;
  if (
    typeof returnTo === "string" &&
    returnTo.startsWith("/") &&
    !returnTo.startsWith("//")
  ) {
    return returnTo;
  }
  return window.location.pathname;
};

root.render(
  <React.StrictMode>
    <Auth0Provider
      domain={process.env.REACT_APP_AUTH0_DOMAIN}
      clientId={process.env.REACT_APP_AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: process.env.REACT_APP_AUTH0_AUDIENCE,
        scope: "openid profile email offline_access",
      }}
      onRedirectCallback={(appState) => {
        window.history.replaceState(
          {},
          document.title,
          getSafeReturnTo(appState),
        );
      }}
      useRefreshTokens={true}
      cacheLocation="localstorage"
    >
      <App />
    </Auth0Provider>
  </React.StrictMode>,
);

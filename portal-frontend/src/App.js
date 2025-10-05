import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import ApplicationPage from "./pages/ApplicationPage";
import ApplicationStatusPage from "./pages/ApplicationStatusPage";
import KellyPage from "./pages/KellyPage";
import "./App.css";
import { FullPageLoadingSpinner } from "./components/FullPageLoadingSpinner";
import { Navbar } from "./components/Navbar";
import NotFound from "./components/404page";

function App() {
  const { isLoading } = useAuth0();
  if (isLoading) {
    return <FullPageLoadingSpinner />;
  }

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/application"
          element={
            <ProtectedRoute>
              <ApplicationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/status"
          element={
            <ProtectedRoute>
              <ApplicationStatusPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/kelly"
          element={
              <KellyPage />
          }
        />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;

import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import FormPage from "./pages/FormPage";
import FormsLandingPage from "./pages/FormsLandingPage";
import ApplicationStatusPage from "./pages/ApplicationStatusPage";
import "./App.css";
import { FullPageLoadingSpinner } from "./components/FullPageLoadingSpinner";
import NotFound from "./components/404page";
import { useInitializeAuth } from "./utils/authUtils";

const DynamicFormPage = () => {
  const params = new URLSearchParams(window.location.search);
  const formKey = params.get("formKey");

  if (!formKey) {
    return <NotFound />;
  }

  return <FormPage formKey={formKey} />;
};

function App() {
  const { isLoading } = useAuth0();
  useInitializeAuth();

  if (isLoading) {
    return <FullPageLoadingSpinner />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/application"
          element={
            <ProtectedRoute>
              <FormsLandingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/form"
          element={
            <ProtectedRoute>
              <DynamicFormPage />
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

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;

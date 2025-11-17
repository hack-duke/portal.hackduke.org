import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import FormPage from "./pages/FormPage";
import ApplicationStatusPage from "./pages/ApplicationStatusPage";
import "./App.css";
import { FullPageLoadingSpinner } from "./components/FullPageLoadingSpinner";
import NotFound from "./components/404page";

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
              <FormPage formKey="2025-cfg-application" />
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

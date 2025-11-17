import React, { useState, useEffect, useMemo } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Navbar } from "../components/Navbar";
import { WhiteBackground } from "../components/WhiteBackground";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Button from "../components/Button";
import { getAllForms } from "../forms/forms";
import "./FormsLandingPage.css";

const FormsLandingPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const navigate = useNavigate();
  const [formsStatus, setFormsStatus] = useState({});
  const [loading, setLoading] = useState(true);

  const allForms = useMemo(() => getAllForms(), []);

  useEffect(() => {
    const fetchAllFormsStatus = async () => {
      setLoading(true);
      const token = await getAccessTokenSilently();
      const statusPromises = allForms.map(async (form) => {
        try {
          const statusRes = await axios.get(
            `${process.env.REACT_APP_BACKEND_URL}/application/form-status`,
            {
              headers: { Authorization: `Bearer ${token}` },
              params: { form_key: form.formKey },
            }
          );

          const isOpen = Boolean(statusRes.data?.is_open);

          let hasSubmitted = false;
          try {
            await axios.get(
              `${process.env.REACT_APP_BACKEND_URL}/application`,
              {
                headers: { Authorization: `Bearer ${token}` },
                params: { form_key: form.formKey },
              }
            );
            hasSubmitted = true;
          } catch (error) {
            if (error.response?.status !== 404) {
              console.error(
                `Error checking submission for ${form.formKey}:`,
                error
              );
            }
          }

          return {
            formKey: form.formKey,
            isOpen,
            hasSubmitted,
          };
        } catch (error) {
          console.error(`Error fetching status for ${form.formKey}:`, error);
          return {
            formKey: form.formKey,
            isOpen: false,
            hasSubmitted: false,
            error: true,
          };
        }
      });

      const results = await Promise.all(statusPromises);
      const statusMap = {};
      results.forEach((result) => {
        statusMap[result.formKey] = result;
      });
      setFormsStatus(statusMap);
      setLoading(false);
    };

    fetchAllFormsStatus();
  }, [getAccessTokenSilently, allForms]);

  const handleFormClick = (formKey) => {
    navigate(`/form?formKey=${formKey}`);
  };

  const handleStatusClick = (formKey) => {
    navigate(`/status?formKey=${formKey}`);
  };

  const getFormCardClass = (formKey) => {
    const status = formsStatus[formKey];
    if (!status) return "form-card";
    if (status.hasSubmitted) return "form-card submitted";
    if (!status.isOpen) return "form-card closed";
    return "form-card open";
  };

  const getStatusBadge = (formKey) => {
    const status = formsStatus[formKey];
    if (!status) return null;
    if (status.hasSubmitted)
      return <span className="badge submitted">Submitted</span>;
    if (status.isOpen) return <span className="badge open">Open</span>;
    return <span className="badge closed">Closed</span>;
  };

  return (
    <>
      <Navbar />
      <WhiteBackground />
      {loading && <FullPageLoadingSpinner />}
      <div className="forms-landing-container">
        <h1 className="forms-landing-title">Applications & Forms</h1>
        <p className="forms-landing-subtitle">
          View and manage your HackDuke applications below.
        </p>

        {!loading && allForms.length === 0 && (
          <div className="no-forms-message">
            <p>No forms are currently available.</p>
            <p>Check back later for new opportunities!</p>
          </div>
        )}

        <div className="forms-grid">
          {allForms.map((form) => {
            const status = formsStatus[form.formKey];
            return (
              <div
                key={form.formKey}
                className={getFormCardClass(form.formKey)}
              >
                <div className="form-card-header">
                  <h2 className="form-card-title">{form.title}</h2>
                  {getStatusBadge(form.formKey)}
                </div>

                <div className="form-card-actions">
                  {status?.hasSubmitted ? (
                    <Button
                      variant="secondary"
                      onClick={() => handleStatusClick(form.formKey)}
                    >
                      View Status
                    </Button>
                  ) : status?.isOpen ? (
                    <Button
                      variant="primary"
                      onClick={() => handleFormClick(form.formKey)}
                    >
                      Apply Now
                    </Button>
                  ) : (
                    <Button variant="tertiary" disabled>
                      Applications Closed
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default FormsLandingPage;

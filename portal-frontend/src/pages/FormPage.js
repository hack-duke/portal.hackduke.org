import React, { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import { MultiPageForm } from "../components/form/Form";
import { Navbar } from "../components/Navbar";
import "./FormPage.css";
import { WhiteBackground } from "../components/WhiteBackground";
import { useNavigate } from "react-router-dom";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Modal, { ModalHeader } from "../components/Modal";
import { getFormByKey } from "../forms/forms";

const FormPage = ({ formKey }) => {
  const { getAccessTokenSilently } = useAuth0();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  const [isFormOpen, setIsFormOpen] = useState(null);

  const formDefinition = getFormByKey(formKey);

  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);
    try {
      let token;
      try {
        token = await getAccessTokenSilently();
      } catch (tokenError) {
        if (tokenError.message.includes("Missing Refresh Token")) {
          // TODO: investigate this error
          openModal();
          setError(
            "Session expired. Please try logging out and logging back in."
          );
          return;
        }
        throw tokenError;
      }

      const formData = new FormData();
      formData.append("form_key", formKey);

      const formDataJson = {};

      for (const [key, value] of Object.entries(data)) {
        if (value instanceof File) {
          formData.append("files", value);
          formDataJson[key] = value.name;
        } else {
          formDataJson[key] = value;
        }
      }

      formData.append("form_data", JSON.stringify(formDataJson));

      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/application/submit`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      navigate("/status", { state: { firstTime: true } });
    } catch (error) {
      openModal();
      setError(error.response?.data?.error);
    }
    setLoading(false);
  };

  useEffect(() => {
    const checkIfSubmitted = async () => {
      try {
        setLoading(true);

        // First check if the form is open
        const tokenForStatus = await getAccessTokenSilently();
        const statusRes = await axios.get(
          `${process.env.REACT_APP_BACKEND_URL}/application/form-status`,
          {
            headers: {
              Authorization: `Bearer ${tokenForStatus}`,
            },
            params: {
              form_key: formKey,
            },
          }
        );

        const open = Boolean(statusRes.data?.is_open);
        setIsFormOpen(open);

        if (!open) {
          return;
        }

        // Existing behavior: if open, check if user already submitted
        const token = await getAccessTokenSilently();
        await axios.get(`${process.env.REACT_APP_BACKEND_URL}/application`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params: {
            form_key: formKey,
          },
        });
        navigate("/status");
      } catch (error) {
        if (error.response?.status !== 404) {
          openModal();
          setError(error.response?.data?.error);
        }
      } finally {
        setLoading(false);
      }
    };

    checkIfSubmitted();
  }, [getAccessTokenSilently, navigate, formKey]);

  // If form doesn't exist, show error
  if (!formDefinition) {
    return (
      <>
        <Navbar />
        <WhiteBackground />
        <div className="notice-container">
          <h1>Form Not Found</h1>
          <p>The form you're looking for doesn't exist.</p>
          <p>
            If you believe this is an error, please reach out to{" "}
            <a href="mailto:hackers@hackduke.org">hackers@hackduke.org</a>
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <WhiteBackground />
      {loading && <FullPageLoadingSpinner />}
      <Modal isOpen={isModalOpen} onClose={closeModal}>
        <ModalHeader>Application Error</ModalHeader>
        <p>{error}</p>
        <p>
          If this error continues to occur, please reach out to{" "}
          <a href="mailto:hackers@hackduke.org">hackers@hackduke.org</a> and we
          will help resolve your issue promptly.
        </p>
      </Modal>

      {/* SHOW when form is CLOSED */}
      {isFormOpen === false && (
        <div className="notice-container">
          <h1>{formDefinition.closedMessage.title}</h1>
          {formDefinition.closedMessage.body}
        </div>
      )}

      {/* SHOW when form is OPEN */}
      {isFormOpen !== false && (
        <div className="form-container">
          <MultiPageForm onSubmit={onSubmit}>
            {formDefinition.renderForm()}
          </MultiPageForm>
        </div>
      )}
    </>
  );
};

export default FormPage;

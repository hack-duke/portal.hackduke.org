import React, { useState, useEffect, useCallback } from "react";
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
import { createGetAuthToken } from "../utils/authUtils";

const FormPage = ({ formKey }) => {
  const { getAccessTokenSilently, user } = useAuth0();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const openModal = useCallback(() => setIsModalOpen(true), []);
  const closeModal = useCallback(() => setIsModalOpen(false), []);

  const [isFormOpen, setIsFormOpen] = useState(null);

  const formDefinition = getFormByKey(formKey);

  const prepareFormData = (data, auth0Email) => {
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
    if (auth0Email) {
      formData.append("auth0_email", auth0Email);
    }
    return formData;
  };

  const submitFormData = async (formData, token) => {
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
  };

  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);

    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, setError);
      const token = await getAuthToken();
      if (!token) {
        return;
      }

      const formData = prepareFormData(data, user?.email);
      await submitFormData(formData, token);

      navigate(`/status?formKey=${formKey}`, { state: { firstTime: true } });
    } catch (err) {
      openModal();
      setError(err.response?.data?.error);
    } finally {
      setLoading(false);
    }
  };

  const checkFormStatus = useCallback(
    async (token, email) => {
      const params = { form_key: formKey };
      if (email) {
        params.email = email;
      }

      const statusRes = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/application/form-status`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params,
        }
      );

      return Boolean(statusRes.data?.is_open);
    },
    [formKey]
  );

  const checkExistingSubmission = useCallback(
    async (token) => {
      await axios.get(`${process.env.REACT_APP_BACKEND_URL}/application`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params: {
          form_key: formKey,
        },
      });
      return true;
    },
    [formKey]
  );

  useEffect(() => {
    const checkIfSubmitted = async () => {
      try {
        setLoading(true);

        const getAuthToken = createGetAuthToken(
          getAccessTokenSilently,
          setError
        );
        const token = await getAuthToken();
        if (!token) {
          return;
        }
        const isOpen = await checkFormStatus(token, user?.email);
        setIsFormOpen(isOpen);

        if (!isOpen) {
          return;
        }

        await checkExistingSubmission(token);

        navigate(`/status?formKey=${formKey}`);
      } catch (err) {
        if (err.response?.status !== 404) {
          openModal();
          setError(err.response?.data?.error);
        }
      } finally {
        setLoading(false);
      }
    };

    checkIfSubmitted();
  }, [
    getAccessTokenSilently,
    navigate,
    formKey,
    checkFormStatus,
    checkExistingSubmission,
    openModal,
    setError,
    user?.email,
  ]);

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

      {isFormOpen && (
        <div className="form-container">
          <MultiPageForm onSubmit={onSubmit}>
            {formDefinition.renderForm()}
          </MultiPageForm>
        </div>
      )}

      {isFormOpen === false && (
        <div className="notice-container">
          <h1>{formDefinition.closedMessage.title}</h1>
          {formDefinition.closedMessage.body}
        </div>
      )}
    </>
  );
};

export default FormPage;

import React, { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import {
  MultiPageForm,
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
} from "../components/form/Form";
import { Navbar } from "../components/Navbar";
import "./ApplicationPage.css";
import { WhiteBackground } from "../components/WhiteBackground";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FullPageLoadingSpinner } from "../components/FullPageLoadingSpinner";
import Modal, { ModalHeader } from "../components/Modal";

const FORM_KEY = "2025-cfg-application";

const ApplicationPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

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
      formData.append("form_key", FORM_KEY);

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
        const token = await getAccessTokenSilently();
        await axios.get(`${process.env.REACT_APP_BACKEND_URL}/application`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params: {
            form_key: FORM_KEY,
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
  }, [getAccessTokenSilently, navigate]);

  return (
    <>
      <Navbar />
      <WhiteBackground />
      {loading && <FullPageLoadingSpinner />}
      <Modal isOpen={isModalOpen} onClose={closeModal}>
        <ModalHeader>Application Submission Error</ModalHeader>
        <p>{error}</p>
        <p>
          If this error continues to occur, please reach out to{" "}
          <a href="mailto:hackers@hackduke.org">hackers@hackduke.org</a> and we
          will help resolve your issue promptly.
        </p>
      </Modal>
      {/* <div className="notice-container">
        <h1>Applications Closed.</h1>
        <p>
          Thank you for your interest in HackDuke Code for Good. The application
          window has now officially closed.{" "}
        </p>
        <p>
          If you believe there was an error with your application, please reach
          out to <a href="mailto:hackers@hackduke.org">hackers@hackduke.org.</a>
        </p>
        <p>Stay tuned for future opportunities!</p>
      </div> */}
      <div className="form-container">
        <MultiPageForm onSubmit={onSubmit}>
          <Page title="General Information">
            <Question name="first_name" label="First Name" required />
            <Question name="last_name" label="Last Name" required />
            <Question name="pref_name" label="Preferred Name" />
            <Question name="email" label="Email" required />
            <Question name="age" type="number" label="Age" required />
            <FileUploadQuestion
              name="resume"
              label="Upload Resume (PDF only)"
              accept="application/pdf"
              required
            />
          </Page>
          <Page title="Education">
            <Question name="country" label="Country of Residence" required />
            <Question name="university" label="University Name" required />
            <Question name="major" label="Major" required />
            <Question
              name="graduation_year"
              label="Graduation Year"
              type="number"
              placeholder="20XX"
              required
            />
            <Question
              name="phone"
              label="Phone Number"
              type="tel"
              placeholder="123-456-7890"
              required
            />
          </Page>
          <Page title="About You">
            <LongQuestion
              name="why_hackduke"
              label="Tell us a bit about why you want to attend HackDuke! What do you hope to learn?"
              rows={5}
              required
            />
            <LongQuestion
              name="why_track"
              label="Which of our four tracks excites you the most? Why?"
              rows={2}
              required
            />
          </Page>
          <Page title="Agreements">
            <CheckQuestion name="community_agr" required>
              I have read and agree to abide by the{" "}
              <a href="https://dukecommunitystandard.students.duke.edu/">
                Duke Community Standard
              </a>{" "}
              during the event.
            </CheckQuestion>
            <CheckQuestion name="photo_agr" required>
              I hereby grant permission for HackDuke and all official sponsors
              to use my photograph and or video in marketing, promotional
              materials, and publications, both online and in print, without
              compensation.
            </CheckQuestion>
            <CheckQuestion name="waiver_agr" required>
              I acknowledge and assume all risks associated with participation,
              releasing the organizers from any liability for injury, loss, or
              damage.
            </CheckQuestion>
          </Page>
          <Page title="Agreements (MLH)">
            <CheckQuestion name="mlh1" required>
              I have read and agree to the{" "}
              <a href="https://github.com/MLH/mlh-policies/blob/main/code-of-conduct.md">
                MLH Code of Conduct
              </a>
              .
            </CheckQuestion>
            <CheckQuestion name="mlh2" required>
              I authorize you to share my application/registration information
              with Major League Hacking for event administration, ranking, and
              MLH administration in-line with the{" "}
              <a href="https://github.com/MLH/mlh-policies/blob/main/privacy-policy.md">
                MLH Privacy Policy
              </a>
              . I further agree to the terms of both the{" "}
              <a href="https://github.com/MLH/mlh-policies/blob/main/contest-terms.md">
                MLH Contest Terms and Conditions
              </a>{" "}
              and the{" "}
              <a href="https://github.com/MLH/mlh-policies/blob/main/privacy-policy.md">
                MLH Privacy Policy
              </a>
              .
            </CheckQuestion>
            <CheckQuestion name="mlh_email_permission">
              I authorize MLH to send me occasional emails about relevant
              events, career opportunities, and community announcements.
            </CheckQuestion>
          </Page>
        </MultiPageForm>
      </div>
    </>
  );
};

export default ApplicationPage;

import React from "react";
import {
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
} from "../components/form/Form";

export const FORMS = {
  "2025-cfg-application": {
    formKey: "2025-cfg-application",
    title: "HackDuke 2025 Application",
    closedMessage: {
      title: "Applications Closed.",
      body: (
        <>
          <p>
            Thank you for your interest in HackDuke Code for Good. The
            application window has now officially closed.{" "}
          </p>
          <p>
            If you believe there was an error with your application, please
            reach out to{" "}
            <a href="mailto:hackers@hackduke.org">hackers@hackduke.org.</a>
          </p>
          <p>Stay tuned for future opportunities!</p>
        </>
      ),
    },
    renderForm: () => [
      <Page key="general" title="General Information">
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
      </Page>,
      <Page key="education" title="Education">
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
      </Page>,
      <Page key="about" title="About You">
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
      </Page>,
      <Page key="agreements" title="Agreements">
        <CheckQuestion name="community_agr" required>
          I have read and agree to abide by the{" "}
          <a href="https://dukecommunitystandard.students.duke.edu/">
            Duke Community Standard
          </a>{" "}
          during the event.
        </CheckQuestion>
        <CheckQuestion name="photo_agr" required>
          I hereby grant permission for HackDuke and all official sponsors to
          use my photograph and or video in marketing, promotional materials,
          and publications, both online and in print, without compensation.
        </CheckQuestion>
        <CheckQuestion name="waiver_agr" required>
          I acknowledge and assume all risks associated with participation,
          releasing the organizers from any liability for injury, loss, or
          damage.
        </CheckQuestion>
      </Page>,
      <Page key="mlh" title="Agreements (MLH)">
        <CheckQuestion name="mlh1" required>
          I have read and agree to the{" "}
          <a href="https://github.com/MLH/mlh-policies/blob/main/code-of-conduct.md">
            MLH Code of Conduct
          </a>
          .
        </CheckQuestion>
        <CheckQuestion name="mlh2" required>
          I authorize you to share my application/registration information with
          Major League Hacking for event administration, ranking, and MLH
          administration in-line with the{" "}
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
          I authorize MLH to send me occasional emails about relevant events,
          career opportunities, and community announcements.
        </CheckQuestion>
      </Page>,
    ],
  },
};

export const getFormByKey = (formKey) => {
  return FORMS[formKey] || null;
};

export const getAllForms = () => {
  return Object.values(FORMS);
};

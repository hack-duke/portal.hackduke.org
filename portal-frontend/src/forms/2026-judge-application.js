import React from "react";
import {
  Page,
  Question,
  LongQuestion,
  CheckQuestion,
  MultipleChoiceQuestion,
} from "../components/form/Form";

export const JUDGE_APPLICATION_2026 = {
  formKey: "2026-judge-application",
  title: "HackDuke 2026 Judge Application",
  closedMessage: {
    title: "Judge Applications Closed.",
    body: (
      <>
        <p>
          Thank you for your interest in being a judge at HackDuke Code for
          Good 2026.
        </p>
        <p>
          If you have any questions, please reach out to{" "}
          <a href="mailto:hackers@hackduke.org">hackers@hackduke.org</a>
        </p>
      </>
    ),
  },
  renderForm: () => [
    <Page key="availability" title="Availability">
      <CheckQuestion name="physical_presence" required>
        I will be physically present at 100 Fuqua Drive (Durham, NC) from 12PM
        to 6PM on Feb 1, 2026 (Sunday).
      </CheckQuestion>
    </Page>,
    <Page key="contact" title="Contact Information">
      <Question name="full_name" label="Full Name" required />
      <Question name="email" label="Email Address" required type="email" />
      <Question
        name="phone"
        label="Phone Number"
        required
        type="tel"
        placeholder="123-456-7890"
      />
      <Question
        name="linkedin_portfolio"
        label="LinkedIn / Website / Portfolio / GitHub"
        placeholder="e.g., https://linkedin.com/in/yourprofile"
      />
    </Page>,
    <Page key="professional" title="Professional Background">
      <Question name="organization" label="Organization / Company / University Affiliation" required />
      <Question name="job_title" label="Job Title / Role" required />
      <LongQuestion
        name="expertise"
        label="What technical or domain expertise do you bring? (e.g., ML/AI, hardware, product, UX/UI, health tech, environmental engineering, public policy, social impact, etc.)"
        rows={4}
        required
      />
      <Question
        name="years_experience"
        label="How many years of experience do you have in your field?"
        type="number"
        required
      />
    </Page>,
    <Page key="judging_experience" title="Judging Experience">
      <LongQuestion
        name="judging_experience"
        label="Describe any experience judging hackathons, pitch competitions, research fairs, or grant reviews."
        rows={4}
        required
      />
      <LongQuestion
        name="valued_aspects"
        label="What aspects of a hackathon project do you value most? (e.g., technical difficulty, creativity, user impact, polish, feasibility, storytelling, teamwork, etc.)"
        rows={4}
        required
      />
      <MultipleChoiceQuestion
        name="feedback_comfort"
        label="How comfortable are you giving constructive, actionable feedback to students?"
        options={["1", "2", "3", "4", "5"]}
        required
      />
    </Page>,
    <Page key="additional_roles" title="Additional Roles & Motivation">
      <MultipleChoiceQuestion
        name="mentor_interest"
        label="Would you like to also be considered as a mentor during the event? Please email hackers@hackduke.org if you are only able to mentor but not judge. You will be contacted individually."
        options={["Yes", "No", "Maybe"]}
        required
      />
      <MultipleChoiceQuestion
        name="workshop_interest"
        label="Would you like to host a workshop during the event? Please email hackers@hackduke.org with your workshop. You will be contacted individually."
        options={["Yes", "No", "Maybe"]}
        required
      />
      <LongQuestion
        name="why_judge"
        label="Why do you want to judge at HackDuke: Code for Good 2026?"
        rows={5}
        required
      />
      <LongQuestion
        name="additional_info"
        label="Anything else you'd like us to know (e.g. reference letter request for O-1)? Please fill 'N/A' otherwise."
        rows={3}
        required
      />
    </Page>,
  ],
};

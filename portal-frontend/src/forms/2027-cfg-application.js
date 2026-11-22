import React from "react";
import {
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
  SelectQuestion,
  PhoneQuestion,
} from "../components/form/Form";
import { COUNTRIES } from "./data/countries";
import { MAJORS, GRADUATION_YEARS } from "./data/majors";

// ~10k schools, so it's split into its own chunk and loaded on first open.
const loadUniversities = () =>
  import("./data/universities.json").then((module) => module.default);

export const CFG_APPLICATION_2027 = {
  formKey: "2027-cfg-application",
  title: "HackDuke 2027 Application",
  closedMessage: {
    title: "Applications Closed.",
    body: (
      <>
        <p>
          Thank you for your interest in HackDuke Code for Good. The application
          window has now officially closed.{" "}
        </p>
        <p>
          If you believe there was an error with your application, please reach
          out to <a href="mailto:hackers@hackduke.org">hackers@hackduke.org.</a>
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
      <SelectQuestion
        name="country"
        label="Country of Residence"
        options={COUNTRIES}
        placeholder="Search countries…"
        required
      />
      <SelectQuestion
        name="graduation_year"
        label="Graduation Year"
        options={GRADUATION_YEARS}
        searchable={false}
        placeholder="Select year"
        required
      />
      <SelectQuestion
        name="university"
        label="University Name"
        options={loadUniversities}
        placeholder="Search for your school…"
        hint="Can't find it? Type the full name and choose “Use …”."
        allowCustom
        fullWidth
        required
      />
      <SelectQuestion
        name="major"
        label="Major(s)"
        options={MAJORS}
        placeholder="Search majors…"
        hint="Select all that apply. Not listed? Type it and choose “Use …”."
        multiple
        allowCustom
        required
      />
      <PhoneQuestion name="phone" label="Phone Number" required />
    </Page>,
    <Page key="about" title="About You">
      <LongQuestion
        name="why_hackduke"
        label="Tell us a bit about why you want to attend HackDuke! What do you hope to learn? (150 words)"
        rows={5}
        maxWords={150}
        required
      />
      <LongQuestion
        name="why_track"
        label="Which of our five tracks excites you the most (Education, Finance, Health, Interactive Media, Sustainability)? Why? (100 words)"
        rows={2}
        maxWords={100}
        required
      />
      <LongQuestion
        name="proud_project"
        label="Tell us about a project that you're proud of, technical or non-technical (150 words)"
        rows={6}
        maxWords={150}
        required
      />
      <LongQuestion
        name="ten_year_vision"
        label="What do you envision yourself doing in the next 10 years? (100 words)"
        rows={4}
        maxWords={100}
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
        I hereby grant permission for HackDuke and all official sponsors to use
        my photograph and or video in marketing, promotional materials, and
        publications, both online and in print, without compensation.
      </CheckQuestion>
      <CheckQuestion name="sponsor_agr" required>
        I hereby grant permission for HackDuke to share resumes and other
        hackathon submission/registration data with all official sponsors.
      </CheckQuestion>
      <CheckQuestion name="waiver_agr" required>
        I acknowledge and assume all risks associated with participation,
        releasing the organizers from any liability for injury, loss, or damage.
      </CheckQuestion>
    </Page>,
  ],
};

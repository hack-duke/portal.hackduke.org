// Example API

/* <MultiPageForm onSubmit={mockSubmit}>
      <Page>
        <Question name="school" label="School:" />
        <Question name="major" label="Major:" />
        <Question name="graduationYear" label="Graduation Year:" type="number" />
      </Page>
      <Page>
        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
      </Page>
</MultiPageForm> */

import { FileUploadQuestion } from "./FileUploadQuestion";
import { Question } from "./Question";
import { Page } from "./Page";
import { MultiPageForm } from "./MultiPageForm";
import { LongQuestion } from "./LongQuestion";
import { CheckQuestion } from "./CheckQuestion";
import { MultipleChoiceQuestion } from "./MultipleChoiceQuestion";

export {
  MultiPageForm,
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
  MultipleChoiceQuestion,
};

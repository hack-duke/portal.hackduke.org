// Example API

/* <SinglePageForm onSubmit={mockSubmit}>
      <Page>
        <Question name="school" label="School:" />
        <Question name="major" label="Major:" />
        <Question name="graduationYear" label="Graduation Year:" type="number" />
      </Page>
      <Page>
        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
      </Page>
</SinglePageForm> */

import { FileUploadQuestion } from "./FileUploadQuestion";
import { Question } from "./Question";
import { Page } from "./Page";
import { SinglePageForm } from "./SinglePageForm";
import { LongQuestion } from "./LongQuestion";
import { CheckQuestion } from "./CheckQuestion";
import { SelectQuestion } from "./SelectQuestion";
import { PhoneQuestion } from "./PhoneQuestion";

export {
  SinglePageForm,
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
  SelectQuestion,
  PhoneQuestion,
};

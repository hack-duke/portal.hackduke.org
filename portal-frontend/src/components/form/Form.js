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

import { FileUploadQuestion } from './FileUploadQuestion';
import { Question } from './Question';
import { Page } from './Page';
import { MultiPageForm } from './MultiPageForm';

export { MultiPageForm, Page, Question, FileUploadQuestion };

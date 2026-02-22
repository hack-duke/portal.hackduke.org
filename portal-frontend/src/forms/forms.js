import axios from "axios";
import { CFG_APPLICATION_2026 } from "./2026-cfg-application";
import {
  Page,
  Question,
  LongQuestion,
  FileUploadQuestion,
  CheckQuestion,
} from "../components/form/Form";

// Hardcoded forms (priority - checked first)
export const HARDCODED_FORMS = {
  [CFG_APPLICATION_2026.formKey]: CFG_APPLICATION_2026,
};

// Fallback to support legacy code
export const FORMS = HARDCODED_FORMS;

/**
 * Get form by key, checking hardcoded forms first, then database forms
 * @param {string} formKey - The form key to fetch
 * @param {string} token - Auth token for API calls
 * @returns {Promise<Object>} Form definition object
 */
export const getFormByKey = async (formKey, token) => {
  // 1. Check hardcoded forms first (priority)
  if (HARDCODED_FORMS[formKey]) {
    return HARDCODED_FORMS[formKey];
  }

  // 2. Try to fetch from database
  try {
    const dbForm = await fetchDbForm(formKey, token);
    if (dbForm) {
      return convertDbFormToReactForm(dbForm);
    }
  } catch (err) {
    console.error(`Failed to fetch database form ${formKey}:`, err);
  }

  // 3. Form not found
  return null;
};

/**
 * Fetch form definition from backend API
 * @param {string} formKey - The form key
 * @param {string} token - Auth token
 * @returns {Promise<Object>} Form details with questions
 */
const fetchDbForm = async (formKey, token) => {
  try {
    const response = await axios.get(
      `${process.env.REACT_APP_BACKEND_URL}/application/form-details`,
      {
        headers: { Authorization: `Bearer ${token}` },
        params: { form_key: formKey },
      }
    );
    return response.data;
  } catch (err) {
    if (err.response?.status === 404) {
      return null; // Form not found
    }
    throw err; // Re-throw other errors
  }
};

/**
 * Convert database form structure to React form component structure
 * @param {Object} dbForm - Form definition from database
 * @returns {Object} Form object with renderForm function
 */
const convertDbFormToReactForm = (dbForm) => {
  const { form, questions } = dbForm;

  // Group questions by page_number
  const pageMap = {};
  questions.forEach((q) => {
    const pageNum = q.page_number || 1;
    if (!pageMap[pageNum]) {
      pageMap[pageNum] = {
        pageNumber: pageNum,
        pageTitle: q.page_title || `Page ${pageNum}`,
        questions: [],
      };
    }
    pageMap[pageNum].questions.push(q);
  });

  // Sort pages and questions within pages
  const pages = Object.values(pageMap).sort(
    (a, b) => a.pageNumber - b.pageNumber
  );

  return {
    formKey: form.form_key,
    title: form.title || "Application Form",
    closedMessage: {
      title: form.closed_message_title || "Form Closed",
      body: form.closed_message_body ? (
        <p>{form.closed_message_body}</p>
      ) : (
        <p>This application form is currently closed.</p>
      ),
    },
    renderForm: () => {
      return pages.map((page) => (
        <Page key={`page-${page.pageNumber}`} title={page.pageTitle}>
          {page.questions
            .sort((a, b) => a.order_in_page - b.order_in_page)
            .map((q) => renderQuestion(q))}
        </Page>
      ));
    },
  };
};

/**
 * Render a question component based on type
 * @param {Object} q - Question data from database
 * @returns {React.ReactNode} Question component
 */
const renderQuestion = (q) => {
  const commonProps = {
    key: q.question_key,
    name: q.question_key,
    label: q.label || q.question_key,
    placeholder: q.placeholder,
    required: q.required || false,
  };

  switch (q.question_type) {
    case "TEXT": {
      // Check if it should be a long text field (textarea)
      if (q.config && q.config.rows) {
        return (
          <LongQuestion
            {...commonProps}
            rows={q.config.rows}
          />
        );
      }
      return <Question {...commonProps} type="text" />;
    }

    case "INTEGER":
      return <Question {...commonProps} type="number" />;

    case "FLOAT":
      return <Question {...commonProps} type="number" step="0.01" />;

    case "BOOLEAN":
      return (
        <CheckQuestion {...commonProps}>
          {q.config?.checkboxText || q.label}
        </CheckQuestion>
      );

    case "FILE":
      return (
        <FileUploadQuestion
          {...commonProps}
          accept={q.config?.accept}
        />
      );

    default:
      return <Question {...commonProps} type="text" />;
  }
};

/**
 * Get all forms (only returns hardcoded forms for now)
 * This is used for listing available forms on the frontend
 * @returns {Array} Array of hardcoded form definitions
 */
export const getAllForms = () => {
  return Object.values(HARDCODED_FORMS);
};

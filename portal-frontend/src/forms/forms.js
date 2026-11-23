import { CFG_APPLICATION_2027 } from "./2027-cfg-application";

export const FORMS = {
  [CFG_APPLICATION_2027.formKey]: CFG_APPLICATION_2027,
};

// The form shown at /application.
export const CURRENT_FORM_KEY = CFG_APPLICATION_2027.formKey;

export const getFormByKey = (formKey) => {
  return FORMS[formKey] || null;
};
